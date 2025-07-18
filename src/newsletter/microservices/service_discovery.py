"""
Microservices Architecture for Newsletter Platform
Implements service discovery, load balancing, and inter-service communication
"""

import asyncio
import logging
import json
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import time
from datetime import datetime, timedelta
import aiohttp
import aioredis
from pydantic import BaseModel, Field
import consul
import etcd3
from fastapi import FastAPI, HTTPException, Depends
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

class ServiceType(str, Enum):
    """Types of microservices"""
    PERSONALIZATION = "personalization"
    CONTENT_CURATION = "content_curation"
    TEMPLATE_GENERATION = "template_generation"
    SEND_TIME_OPTIMIZATION = "send_time_optimization"
    ANALYTICS = "analytics"
    AUTOMATION = "automation"
    PRIVACY = "privacy"
    NOTIFICATION = "notification"

class ServiceStatus(str, Enum):
    """Service status states"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    STARTING = "starting"
    STOPPING = "stopping"
    UNKNOWN = "unknown"

@dataclass
class ServiceInstance:
    """Service instance metadata"""
    service_id: str
    service_type: ServiceType
    host: str
    port: int
    version: str
    status: ServiceStatus
    registered_at: datetime
    last_heartbeat: datetime
    metadata: Dict[str, Any]
    health_check_url: str
    load_factor: float = 0.0

@dataclass
class ServiceCall:
    """Service call tracking"""
    call_id: str
    source_service: str
    target_service: str
    method: str
    endpoint: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    success: bool = False
    response_time_ms: float = 0.0
    error: Optional[str] = None

class ServiceRegistry:
    """Service registry for microservices discovery"""
    
    def __init__(self, redis_client: aioredis.Redis, consul_client: Optional[consul.Consul] = None):
        self.redis = redis_client
        self.consul = consul_client
        self.services: Dict[str, ServiceInstance] = {}
        self.registry_key = "microservices:registry"
        self.heartbeat_interval = 30  # seconds
        self.service_timeout = 90  # seconds
        self.cleanup_task = None
        
    async def register_service(
        self,
        service_type: ServiceType,
        host: str,
        port: int,
        version: str = "1.0.0",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Register a service instance"""
        try:
            service_id = f"{service_type.value}-{uuid.uuid4().hex[:8]}"
            
            instance = ServiceInstance(
                service_id=service_id,
                service_type=service_type,
                host=host,
                port=port,
                version=version,
                status=ServiceStatus.STARTING,
                registered_at=datetime.utcnow(),
                last_heartbeat=datetime.utcnow(),
                metadata=metadata or {},
                health_check_url=f"http://{host}:{port}/health"
            )
            
            # Store in Redis
            await self.redis.hset(
                self.registry_key,
                service_id,
                json.dumps(asdict(instance), default=str)
            )
            
            # Store locally
            self.services[service_id] = instance
            
            # Register with Consul if available
            if self.consul:
                await self._register_with_consul(instance)
            
            logger.info(f"Service registered: {service_id} ({service_type.value})")
            return service_id
            
        except Exception as e:
            logger.error(f"Failed to register service: {e}")
            raise
    
    async def deregister_service(self, service_id: str):
        """Deregister a service instance"""
        try:
            # Remove from Redis
            await self.redis.hdel(self.registry_key, service_id)
            
            # Remove locally
            if service_id in self.services:
                instance = self.services[service_id]
                del self.services[service_id]
                
                # Deregister from Consul if available
                if self.consul:
                    await self._deregister_from_consul(instance)
            
            logger.info(f"Service deregistered: {service_id}")
            
        except Exception as e:
            logger.error(f"Failed to deregister service: {e}")
    
    async def heartbeat(self, service_id: str, load_factor: float = 0.0):
        """Send heartbeat for a service"""
        try:
            if service_id in self.services:
                instance = self.services[service_id]
                instance.last_heartbeat = datetime.utcnow()
                instance.status = ServiceStatus.HEALTHY
                instance.load_factor = load_factor
                
                # Update in Redis
                await self.redis.hset(
                    self.registry_key,
                    service_id,
                    json.dumps(asdict(instance), default=str)
                )
                
                logger.debug(f"Heartbeat received from {service_id}")
            
        except Exception as e:
            logger.error(f"Failed to process heartbeat: {e}")
    
    async def discover_services(
        self,
        service_type: ServiceType,
        healthy_only: bool = True
    ) -> List[ServiceInstance]:
        """Discover services of a specific type"""
        try:
            # Get all services from Redis
            services_data = await self.redis.hgetall(self.registry_key)
            
            instances = []
            for service_id, data in services_data.items():
                try:
                    service_dict = json.loads(data)
                    instance = ServiceInstance(**service_dict)
                    
                    # Convert string timestamps back to datetime
                    instance.registered_at = datetime.fromisoformat(instance.registered_at)
                    instance.last_heartbeat = datetime.fromisoformat(instance.last_heartbeat)
                    
                    # Filter by type
                    if instance.service_type == service_type:
                        # Check if service is healthy
                        if healthy_only:
                            if self._is_service_healthy(instance):
                                instances.append(instance)
                        else:
                            instances.append(instance)
                            
                except Exception as e:
                    logger.error(f"Failed to parse service data for {service_id}: {e}")
            
            return instances
            
        except Exception as e:
            logger.error(f"Failed to discover services: {e}")
            return []
    
    async def get_service_instance(self, service_id: str) -> Optional[ServiceInstance]:
        """Get specific service instance"""
        try:
            data = await self.redis.hget(self.registry_key, service_id)
            if data:
                service_dict = json.loads(data)
                instance = ServiceInstance(**service_dict)
                instance.registered_at = datetime.fromisoformat(instance.registered_at)
                instance.last_heartbeat = datetime.fromisoformat(instance.last_heartbeat)
                return instance
            return None
            
        except Exception as e:
            logger.error(f"Failed to get service instance: {e}")
            return None
    
    async def start_cleanup_task(self):
        """Start background task to cleanup stale services"""
        if self.cleanup_task is None:
            self.cleanup_task = asyncio.create_task(self._cleanup_stale_services())
    
    async def stop_cleanup_task(self):
        """Stop cleanup task"""
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
            self.cleanup_task = None
    
    def _is_service_healthy(self, instance: ServiceInstance) -> bool:
        """Check if service is healthy based on last heartbeat"""
        time_since_heartbeat = datetime.utcnow() - instance.last_heartbeat
        return time_since_heartbeat.total_seconds() < self.service_timeout
    
    async def _cleanup_stale_services(self):
        """Background task to cleanup stale services"""
        while True:
            try:
                services_data = await self.redis.hgetall(self.registry_key)
                
                for service_id, data in services_data.items():
                    try:
                        service_dict = json.loads(data)
                        instance = ServiceInstance(**service_dict)
                        instance.last_heartbeat = datetime.fromisoformat(instance.last_heartbeat)
                        
                        if not self._is_service_healthy(instance):
                            logger.warning(f"Removing stale service: {service_id}")
                            await self.deregister_service(service_id)
                            
                    except Exception as e:
                        logger.error(f"Error checking service {service_id}: {e}")
                
                await asyncio.sleep(60)  # Check every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
                await asyncio.sleep(60)
    
    async def _register_with_consul(self, instance: ServiceInstance):
        """Register service with Consul"""
        if not self.consul:
            return
            
        try:
            check = consul.Check.http(
                instance.health_check_url,
                interval="30s",
                timeout="10s"
            )
            
            self.consul.agent.service.register(
                name=instance.service_type.value,
                service_id=instance.service_id,
                address=instance.host,
                port=instance.port,
                tags=[f"version:{instance.version}"],
                check=check
            )
            
        except Exception as e:
            logger.error(f"Failed to register with Consul: {e}")
    
    async def _deregister_from_consul(self, instance: ServiceInstance):
        """Deregister service from Consul"""
        if not self.consul:
            return
            
        try:
            self.consul.agent.service.deregister(instance.service_id)
        except Exception as e:
            logger.error(f"Failed to deregister from Consul: {e}")

class LoadBalancer:
    """Load balancer for microservices"""
    
    def __init__(self, service_registry: ServiceRegistry):
        self.registry = service_registry
        self.call_history: Dict[str, List[ServiceCall]] = {}
        
    async def get_best_instance(
        self,
        service_type: ServiceType,
        strategy: str = "round_robin"
    ) -> Optional[ServiceInstance]:
        """Get the best service instance based on load balancing strategy"""
        try:
            instances = await self.registry.discover_services(service_type, healthy_only=True)
            
            if not instances:
                return None
            
            if strategy == "round_robin":
                return self._round_robin_selection(instances)
            elif strategy == "least_loaded":
                return self._least_loaded_selection(instances)
            elif strategy == "fastest_response":
                return self._fastest_response_selection(instances)
            else:
                # Default to round robin
                return self._round_robin_selection(instances)
                
        except Exception as e:
            logger.error(f"Failed to get best instance: {e}")
            return None
    
    def _round_robin_selection(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """Round robin load balancing"""
        # Simple implementation - can be enhanced with persistent state
        return instances[int(time.time()) % len(instances)]
    
    def _least_loaded_selection(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """Select instance with lowest load factor"""
        return min(instances, key=lambda x: x.load_factor)
    
    def _fastest_response_selection(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """Select instance with fastest average response time"""
        best_instance = instances[0]
        best_avg_time = float('inf')
        
        for instance in instances:
            avg_time = self._get_average_response_time(instance.service_id)
            if avg_time < best_avg_time:
                best_avg_time = avg_time
                best_instance = instance
        
        return best_instance
    
    def _get_average_response_time(self, service_id: str) -> float:
        """Get average response time for a service"""
        calls = self.call_history.get(service_id, [])
        if not calls:
            return 0.0
        
        # Consider only recent calls (last 100)
        recent_calls = calls[-100:]
        successful_calls = [call for call in recent_calls if call.success]
        
        if not successful_calls:
            return float('inf')
        
        total_time = sum(call.response_time_ms for call in successful_calls)
        return total_time / len(successful_calls)
    
    async def record_call(self, call: ServiceCall):
        """Record a service call for performance tracking"""
        service_id = call.target_service
        
        if service_id not in self.call_history:
            self.call_history[service_id] = []
        
        self.call_history[service_id].append(call)
        
        # Keep only recent history (last 1000 calls)
        if len(self.call_history[service_id]) > 1000:
            self.call_history[service_id] = self.call_history[service_id][-1000:]

class ServiceClient:
    """HTTP client for inter-service communication"""
    
    def __init__(self, service_registry: ServiceRegistry, load_balancer: LoadBalancer):
        self.registry = service_registry
        self.load_balancer = load_balancer
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            connector=aiohttp.TCPConnector(limit=100)
        )
        
    async def call_service(
        self,
        service_type: ServiceType,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: float = 30.0,
        retries: int = 3
    ) -> Dict[str, Any]:
        """Make a call to a microservice with retries and load balancing"""
        
        call = ServiceCall(
            call_id=str(uuid.uuid4()),
            source_service="newsletter-api",
            target_service=service_type.value,
            method=method,
            endpoint=endpoint,
            started_at=datetime.utcnow()
        )
        
        last_error = None
        
        for attempt in range(retries):
            try:
                # Get best instance
                instance = await self.load_balancer.get_best_instance(service_type)
                if not instance:
                    raise HTTPException(
                        status_code=503,
                        detail=f"No healthy instances available for {service_type.value}"
                    )
                
                # Construct URL
                url = f"http://{instance.host}:{instance.port}{endpoint}"
                
                # Prepare headers
                call_headers = {
                    "Content-Type": "application/json",
                    "X-Call-ID": call.call_id,
                    "X-Source-Service": call.source_service,
                    **(headers or {})
                }
                
                # Make request
                start_time = time.time()
                
                async with self.session.request(
                    method,
                    url,
                    json=data,
                    headers=call_headers,
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    if response.status >= 400:
                        error_text = await response.text()
                        raise aiohttp.ClientResponseError(
                            request_info=response.request_info,
                            history=response.history,
                            status=response.status,
                            message=error_text
                        )
                    
                    result = await response.json()
                    
                    # Record successful call
                    call.completed_at = datetime.utcnow()
                    call.success = True
                    call.response_time_ms = response_time
                    
                    await self.load_balancer.record_call(call)
                    
                    logger.debug(f"Service call successful: {service_type.value}/{endpoint} in {response_time:.2f}ms")
                    return result
                    
            except Exception as e:
                last_error = e
                logger.warning(f"Service call attempt {attempt + 1} failed: {e}")
                
                if attempt < retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        # Record failed call
        call.completed_at = datetime.utcnow()
        call.success = False
        call.error = str(last_error)
        
        await self.load_balancer.record_call(call)
        
        logger.error(f"Service call failed after {retries} attempts: {last_error}")
        raise HTTPException(
            status_code=503,
            detail=f"Service {service_type.value} unavailable after {retries} attempts"
        )
    
    async def close(self):
        """Close the HTTP session"""
        await self.session.close()

class MicroserviceBase:
    """Base class for microservices"""
    
    def __init__(
        self,
        service_type: ServiceType,
        host: str = "localhost",
        port: int = 8000,
        version: str = "1.0.0"
    ):
        self.service_type = service_type
        self.host = host
        self.port = port
        self.version = version
        self.service_id = None
        self.registry = None
        self.heartbeat_task = None
        
        # Create FastAPI app
        self.app = FastAPI(
            title=f"{service_type.value.title()} Service",
            version=version,
            lifespan=self.lifespan
        )
        
        # Add health check endpoint
        self.app.get("/health")(self.health_check)
        
    @asynccontextmanager
    async def lifespan(self, app: FastAPI):
        """Lifespan manager for service startup/shutdown"""
        # Startup
        await self.startup()
        yield
        # Shutdown
        await self.shutdown()
    
    async def startup(self):
        """Service startup logic"""
        try:
            # Initialize Redis connection
            redis_client = aioredis.from_url("redis://localhost:6379")
            
            # Initialize service registry
            self.registry = ServiceRegistry(redis_client)
            
            # Register service
            self.service_id = await self.registry.register_service(
                service_type=self.service_type,
                host=self.host,
                port=self.port,
                version=self.version,
                metadata=await self.get_service_metadata()
            )
            
            # Start heartbeat task
            self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            
            logger.info(f"{self.service_type.value} service started: {self.service_id}")
            
        except Exception as e:
            logger.error(f"Failed to start service: {e}")
            raise
    
    async def shutdown(self):
        """Service shutdown logic"""
        try:
            # Stop heartbeat
            if self.heartbeat_task:
                self.heartbeat_task.cancel()
                try:
                    await self.heartbeat_task
                except asyncio.CancelledError:
                    pass
            
            # Deregister service
            if self.registry and self.service_id:
                await self.registry.deregister_service(self.service_id)
            
            logger.info(f"{self.service_type.value} service stopped")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
    async def health_check(self):
        """Health check endpoint"""
        return {
            "status": "healthy",
            "service_type": self.service_type.value,
            "service_id": self.service_id,
            "timestamp": datetime.utcnow().isoformat(),
            "version": self.version
        }
    
    async def get_service_metadata(self) -> Dict[str, Any]:
        """Get service-specific metadata"""
        return {
            "capabilities": [],
            "dependencies": [],
            "configuration": {}
        }
    
    async def _heartbeat_loop(self):
        """Send periodic heartbeats"""
        while True:
            try:
                load_factor = await self.get_load_factor()
                await self.registry.heartbeat(self.service_id, load_factor)
                await asyncio.sleep(30)  # Heartbeat every 30 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                await asyncio.sleep(30)
    
    async def get_load_factor(self) -> float:
        """Get current load factor (0.0 to 1.0)"""
        # Override in subclasses to provide actual load metrics
        return 0.0

# Global instances
service_registry = None
load_balancer = None
service_client = None

async def initialize_microservices(redis_client: aioredis.Redis):
    """Initialize microservices infrastructure"""
    global service_registry, load_balancer, service_client
    
    service_registry = ServiceRegistry(redis_client)
    load_balancer = LoadBalancer(service_registry)
    service_client = ServiceClient(service_registry, load_balancer)
    
    # Start cleanup task
    await service_registry.start_cleanup_task()
    
    logger.info("Microservices infrastructure initialized")

async def shutdown_microservices():
    """Shutdown microservices infrastructure"""
    global service_registry, load_balancer, service_client
    
    if service_client:
        await service_client.close()
    
    if service_registry:
        await service_registry.stop_cleanup_task()
    
    logger.info("Microservices infrastructure shutdown")

def get_service_client() -> ServiceClient:
    """Get global service client"""
    global service_client
    if service_client is None:
        raise RuntimeError("Microservices not initialized")
    return service_client
