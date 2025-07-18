"""
Adaptive Template Engine - Dynamic Email Template Generation
Creates personalized email templates that adapt to user preferences and behavior.
"""

import asyncio
import json
import logging
import jinja2
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import re
from pathlib import Path

from src.core.logging import StructuredLogger
from src.core.cache import AsyncCacheManager
from src.newsletter.core.personalization_engine import UserPersona, ContentType
from src.newsletter.core.content_curator import ContentItem


class TemplateStyle(Enum):
    """Email template styles"""
    MINIMAL = "minimal"
    CLASSIC = "classic"
    MODERN = "modern"
    MAGAZINE = "magazine"
    NEWSLETTER = "newsletter"
    PERSONAL = "personal"


class LayoutType(Enum):
    """Template layout types"""
    SINGLE_COLUMN = "single_column"
    TWO_COLUMN = "two_column"
    CARD_GRID = "card_grid"
    LIST_VIEW = "list_view"
    MASONRY = "masonry"


class ColorScheme(Enum):
    """Color schemes for templates"""
    LIGHT = "light"
    DARK = "dark"
    BLUE = "blue"
    GREEN = "green"
    WARM = "warm"
    MINIMAL = "minimal"


@dataclass
class TemplateConfig:
    """Template configuration"""
    style: TemplateStyle
    layout: LayoutType
    color_scheme: ColorScheme
    font_family: str
    font_size: str
    header_style: str
    footer_style: str
    content_density: str  # sparse, normal, dense
    image_style: str  # full, thumbnail, none
    call_to_action_style: str
    personalization_level: str
    mobile_optimized: bool = True
    accessibility_features: bool = True


@dataclass
class TemplateData:
    """Data for template rendering"""
    user_persona: UserPersona
    content_items: List[ContentItem]
    subject_line: str
    preheader_text: str
    sender_name: str
    sender_email: str
    unsubscribe_url: str
    preferences_url: str
    branding: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RenderedTemplate:
    """Rendered email template"""
    html_content: str
    text_content: str
    subject_line: str
    preheader_text: str
    template_version: str
    personalization_tokens: Dict[str, str]
    rendering_time: float
    template_config: TemplateConfig
    metadata: Dict[str, Any] = field(default_factory=dict)


class AdaptiveTemplateEngine:
    """
    Adaptive Template Engine
    
    Features:
    - Dynamic template selection based on user preferences
    - Responsive design adaptation
    - A/B testing for template variations
    - Accessibility optimization
    - Performance optimization
    - Multi-language support
    """
    
    def __init__(
        self,
        cache_manager: AsyncCacheManager,
        template_dir: str = "templates/email"
    ):
        self.cache = cache_manager
        self.template_dir = Path(template_dir)
        self.logger = StructuredLogger(__name__)
        
        # Jinja2 environment
        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(self.template_dir)),
            autoescape=jinja2.select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Template cache
        self.template_cache: Dict[str, jinja2.Template] = {}
        
        # User template preferences
        self.user_preferences: Dict[str, TemplateConfig] = {}
        
        # A/B testing configurations
        self.ab_tests: Dict[str, List[TemplateConfig]] = {}
        
        # Performance metrics
        self.template_performance: Dict[str, Dict[str, float]] = {}
    
    async def render_personalized_template(
        self,
        template_data: TemplateData,
        template_config: Optional[TemplateConfig] = None
    ) -> RenderedTemplate:
        """Render personalized email template"""
        start_time = datetime.utcnow()
        
        try:
            # Get or determine template configuration
            if not template_config:
                template_config = await self._determine_optimal_template_config(
                    template_data.user_persona
                )
            
            # Generate subject line if not provided
            if not template_data.subject_line:
                template_data.subject_line = await self._generate_subject_line(
                    template_data, template_config
                )
            
            # Generate preheader if not provided
            if not template_data.preheader_text:
                template_data.preheader_text = await self._generate_preheader(
                    template_data, template_config
                )
            
            # Prepare template context
            context = await self._prepare_template_context(template_data, template_config)
            
            # Render HTML content
            html_content = await self._render_html_template(context, template_config)
            
            # Generate text content
            text_content = await self._generate_text_content(context, template_config)
            
            # Apply personalization tokens
            personalization_tokens = await self._generate_personalization_tokens(
                template_data.user_persona
            )
            
            html_content = await self._apply_personalization(html_content, personalization_tokens)
            text_content = await self._apply_personalization(text_content, personalization_tokens)
            
            # Calculate rendering time
            rendering_time = (datetime.utcnow() - start_time).total_seconds()
            
            rendered_template = RenderedTemplate(
                html_content=html_content,
                text_content=text_content,
                subject_line=template_data.subject_line,
                preheader_text=template_data.preheader_text,
                template_version=self._get_template_version(template_config),
                personalization_tokens=personalization_tokens,
                rendering_time=rendering_time,
                template_config=template_config,
                metadata={
                    "content_items": len(template_data.content_items),
                    "personalization_level": template_config.personalization_level,
                    "user_id": template_data.user_persona.user_id
                }
            )
            
            # Cache rendered template
            await self._cache_rendered_template(rendered_template, template_data)
            
            self.logger.info(
                "Template rendered successfully",
                user_id=template_data.user_persona.user_id,
                template_style=template_config.style.value,
                rendering_time=rendering_time,
                content_items=len(template_data.content_items)
            )
            
            return rendered_template
            
        except Exception as e:
            self.logger.error(
                "Template rendering failed",
                user_id=template_data.user_persona.user_id,
                error=str(e)
            )
            # Return fallback template
            return await self._render_fallback_template(template_data)
    
    async def optimize_template_for_user(
        self,
        user_persona: UserPersona,
        engagement_history: List[Dict[str, Any]]
    ) -> TemplateConfig:
        """Optimize template configuration based on user engagement"""
        try:
            # Analyze engagement patterns
            engagement_analysis = await self._analyze_template_engagement(
                user_persona.user_id, engagement_history
            )
            
            # Determine optimal configuration
            optimal_config = await self._calculate_optimal_config(
                user_persona, engagement_analysis
            )
            
            # Cache user preferences
            self.user_preferences[user_persona.user_id] = optimal_config
            
            # Update cache
            cache_key = f"template_config:{user_persona.user_id}"
            await self.cache.set(
                cache_key,
                json.dumps(optimal_config.__dict__, default=str),
                ttl=604800  # 1 week
            )
            
            self.logger.info(
                "Template optimized for user",
                user_id=user_persona.user_id,
                style=optimal_config.style.value,
                layout=optimal_config.layout.value,
                color_scheme=optimal_config.color_scheme.value
            )
            
            return optimal_config
            
        except Exception as e:
            self.logger.error(
                "Template optimization failed",
                user_id=user_persona.user_id,
                error=str(e)
            )
            return await self._get_default_template_config(user_persona)
    
    async def create_ab_test_variants(
        self,
        base_config: TemplateConfig,
        test_parameters: List[str]
    ) -> List[TemplateConfig]:
        """Create A/B test variants"""
        try:
            variants = [base_config]  # Control
            
            for param in test_parameters:
                variant_config = await self._create_variant_config(base_config, param)
                variants.append(variant_config)
            
            self.logger.info(
                "A/B test variants created",
                base_style=base_config.style.value,
                variants_count=len(variants),
                test_parameters=test_parameters
            )
            
            return variants
            
        except Exception as e:
            self.logger.error(
                "A/B test variant creation failed",
                error=str(e)
            )
            return [base_config]
    
    async def analyze_template_performance(
        self,
        template_configs: List[TemplateConfig],
        performance_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze template performance metrics"""
        try:
            analysis = {
                "total_sends": len(performance_data),
                "config_performance": {},
                "best_performing": None,
                "insights": []
            }
            
            # Group by template configuration
            config_groups = {}
            for data in performance_data:
                config_id = data.get("template_version", "unknown")
                if config_id not in config_groups:
                    config_groups[config_id] = []
                config_groups[config_id].append(data)
            
            # Calculate metrics for each configuration
            for config_id, group_data in config_groups.items():
                if not group_data:
                    continue
                
                metrics = {
                    "sends": len(group_data),
                    "open_rate": sum(d.get("opened", 0) for d in group_data) / len(group_data),
                    "click_rate": sum(d.get("clicked", 0) for d in group_data) / len(group_data),
                    "engagement_rate": sum(d.get("engagement_rate", 0) for d in group_data) / len(group_data),
                    "unsubscribe_rate": sum(d.get("unsubscribed", 0) for d in group_data) / len(group_data)
                }
                
                analysis["config_performance"][config_id] = metrics
            
            # Find best performing configuration
            if analysis["config_performance"]:
                best_config = max(
                    analysis["config_performance"].items(),
                    key=lambda x: x[1]["engagement_rate"]
                )
                analysis["best_performing"] = {
                    "config_id": best_config[0],
                    "metrics": best_config[1]
                }
            
            # Generate insights
            analysis["insights"] = await self._generate_performance_insights(analysis)
            
            self.logger.info(
                "Template performance analyzed",
                total_sends=analysis["total_sends"],
                configurations=len(analysis["config_performance"]),
                best_config=analysis["best_performing"]["config_id"] if analysis["best_performing"] else None
            )
            
            return analysis
            
        except Exception as e:
            self.logger.error(
                "Template performance analysis failed",
                error=str(e)
            )
            return {}
    
    # Private helper methods
    
    async def _determine_optimal_template_config(
        self,
        user_persona: UserPersona
    ) -> TemplateConfig:
        """Determine optimal template configuration for user"""
        # Check cached preferences
        if user_persona.user_id in self.user_preferences:
            return self.user_preferences[user_persona.user_id]
        
        # Check cache
        cache_key = f"template_config:{user_persona.user_id}"
        cached_config = await self.cache.get(cache_key)
        if cached_config:
            config_data = json.loads(cached_config)
            return TemplateConfig(**config_data)
        
        # Generate new configuration based on persona
        return await self._generate_config_from_persona(user_persona)
    
    async def _generate_config_from_persona(
        self,
        user_persona: UserPersona
    ) -> TemplateConfig:
        """Generate template config based on user persona"""
        # Style selection based on behavioral clusters
        if "minimalist" in user_persona.behavioral_clusters:
            style = TemplateStyle.MINIMAL
        elif "design_conscious" in user_persona.behavioral_clusters:
            style = TemplateStyle.MODERN
        elif "traditional" in user_persona.behavioral_clusters:
            style = TemplateStyle.CLASSIC
        else:
            style = TemplateStyle.NEWSLETTER
        
        # Layout based on attention span
        if user_persona.attention_span == "short":
            layout = LayoutType.SINGLE_COLUMN
        elif user_persona.attention_span == "long":
            layout = LayoutType.TWO_COLUMN
        else:
            layout = LayoutType.CARD_GRID
        
        # Color scheme based on content preferences
        if user_persona.content_preferences.get(ContentType.PERSONALIZED_QUOTES, 0) > 0.7:
            color_scheme = ColorScheme.WARM
        elif user_persona.content_preferences.get(ContentType.TRENDING_TOPICS, 0) > 0.7:
            color_scheme = ColorScheme.BLUE
        else:
            color_scheme = ColorScheme.LIGHT
        
        # Content density based on reading velocity
        if user_persona.reading_velocity > 3.0:
            content_density = "dense"
        elif user_persona.reading_velocity < 1.0:
            content_density = "sparse"
        else:
            content_density = "normal"
        
        return TemplateConfig(
            style=style,
            layout=layout,
            color_scheme=color_scheme,
            font_family="Inter, sans-serif",
            font_size="16px",
            header_style="modern",
            footer_style="minimal",
            content_density=content_density,
            image_style="thumbnail",
            call_to_action_style="button",
            personalization_level="high",
            mobile_optimized=True,
            accessibility_features=True
        )
    
    async def _prepare_template_context(
        self,
        template_data: TemplateData,
        template_config: TemplateConfig
    ) -> Dict[str, Any]:
        """Prepare context for template rendering"""
        context = {
            # User data
            "user": {
                "name": template_data.user_persona.user_id,  # Would be actual name in production
                "reading_velocity": template_data.user_persona.reading_velocity,
                "preferred_genres": template_data.user_persona.preferred_genres,
                "engagement_pattern": template_data.user_persona.engagement_pattern,
                "attention_span": template_data.user_persona.attention_span
            },
            
            # Content
            "content_items": template_data.content_items,
            "content_count": len(template_data.content_items),
            
            # Email metadata
            "subject": template_data.subject_line,
            "preheader": template_data.preheader_text,
            "sender_name": template_data.sender_name,
            "sender_email": template_data.sender_email,
            
            # URLs
            "unsubscribe_url": template_data.unsubscribe_url,
            "preferences_url": template_data.preferences_url,
            
            # Branding
            "branding": template_data.branding,
            
            # Template configuration
            "config": template_config,
            
            # Current date
            "current_date": datetime.utcnow().strftime("%B %d, %Y"),
            "current_year": datetime.utcnow().year,
            
            # Personalization
            "is_personalized": True,
            "personalization_level": template_config.personalization_level,
            
            # Metadata
            "metadata": template_data.metadata
        }
        
        # Add content type groupings
        content_by_type = {}
        for item in template_data.content_items:
            if item.type not in content_by_type:
                content_by_type[item.type] = []
            content_by_type[item.type].append(item)
        
        context["content_by_type"] = content_by_type
        
        return context
    
    async def _render_html_template(
        self,
        context: Dict[str, Any],
        template_config: TemplateConfig
    ) -> str:
        """Render HTML template"""
        template_name = f"{template_config.style.value}_{template_config.layout.value}.html"
        
        # Get or load template
        if template_name not in self.template_cache:
            try:
                self.template_cache[template_name] = self.jinja_env.get_template(template_name)
            except jinja2.TemplateNotFound:
                # Fall back to base template
                template_name = "base_newsletter.html"
                self.template_cache[template_name] = self.jinja_env.get_template(template_name)
        
        template = self.template_cache[template_name]
        return template.render(**context)
    
    async def _generate_text_content(
        self,
        context: Dict[str, Any],
        template_config: TemplateConfig
    ) -> str:
        """Generate plain text version"""
        text_parts = []
        
        # Header
        text_parts.append(f"📚 {context['sender_name']}")
        text_parts.append("=" * 50)
        text_parts.append("")
        
        # Personalized greeting
        user_name = context["user"]["name"]
        text_parts.append(f"Hello {user_name},")
        text_parts.append("")
        
        # Content items
        for item in context["content_items"]:
            text_parts.append(f"📖 {item.title}")
            text_parts.append(f"   {item.description}")
            if hasattr(item, 'personalization_reasons') and item.personalization_reasons:
                text_parts.append(f"   💡 {item.personalization_reasons[0]}")
            text_parts.append("")
        
        # Footer
        text_parts.append("-" * 50)
        text_parts.append("Happy reading!")
        text_parts.append("")
        text_parts.append(f"Unsubscribe: {context['unsubscribe_url']}")
        text_parts.append(f"Update preferences: {context['preferences_url']}")
        
        return "\n".join(text_parts)
    
    async def _generate_subject_line(
        self,
        template_data: TemplateData,
        template_config: TemplateConfig
    ) -> str:
        """Generate personalized subject line"""
        # Get primary content item
        if not template_data.content_items:
            return "Your personalized reading recommendations"
        
        primary_item = template_data.content_items[0]
        user_name = template_data.user_persona.user_id  # Would be actual name
        
        # Subject line templates based on content type
        subject_templates = {
            ContentType.BOOK_RECOMMENDATION: [
                f"📚 {user_name}, we found your next great read",
                f"Your personalized book recommendations are here",
                f"New books matched to your taste, {user_name}"
            ],
            ContentType.TRENDING_TOPICS: [
                f"🔥 What's trending in your reading world",
                f"Hot topics every reader is talking about",
                f"Don't miss these trending reads, {user_name}"
            ],
            ContentType.READING_INSIGHTS: [
                f"💡 Your reading insights for {datetime.utcnow().strftime('%B')}",
                f"Discover patterns in your reading journey",
                f"Personal reading analytics inside"
            ]
        }
        
        templates = subject_templates.get(
            primary_item.type,
            ["Your personalized newsletter is ready"]
        )
        
        # Select based on user preference (simplified)
        return templates[0]  # Would use ML model in production
    
    async def _generate_preheader(
        self,
        template_data: TemplateData,
        template_config: TemplateConfig
    ) -> str:
        """Generate preheader text"""
        if not template_data.content_items:
            return "Discover your next favorite book with personalized recommendations"
        
        content_count = len(template_data.content_items)
        primary_type = template_data.content_items[0].type
        
        preheader_templates = {
            ContentType.BOOK_RECOMMENDATION: f"{content_count} books selected just for you",
            ContentType.TRENDING_TOPICS: f"See what's capturing readers' attention today",
            ContentType.READING_INSIGHTS: f"Your reading patterns and recommendations"
        }
        
        return preheader_templates.get(
            primary_type,
            f"Your personalized content: {content_count} items inside"
        )
    
    async def _generate_personalization_tokens(
        self,
        user_persona: UserPersona
    ) -> Dict[str, str]:
        """Generate personalization tokens"""
        return {
            "{{USER_NAME}}": user_persona.user_id,  # Would be actual name
            "{{READING_VELOCITY}}": f"{user_persona.reading_velocity:.1f}",
            "{{PREFERRED_GENRES}}": ", ".join(user_persona.preferred_genres[:3]),
            "{{ENGAGEMENT_PATTERN}}": user_persona.engagement_pattern,
            "{{TOTAL_GENRES}}": str(len(user_persona.preferred_genres)),
            "{{READING_LEVEL}}": self._get_reading_level_description(user_persona.reading_velocity)
        }
    
    def _get_reading_level_description(self, velocity: float) -> str:
        """Get reading level description"""
        if velocity > 3.0:
            return "voracious reader"
        elif velocity > 2.0:
            return "avid reader"
        elif velocity > 1.0:
            return "regular reader"
        else:
            return "casual reader"
    
    async def _apply_personalization(
        self,
        content: str,
        tokens: Dict[str, str]
    ) -> str:
        """Apply personalization tokens to content"""
        for token, value in tokens.items():
            content = content.replace(token, value)
        return content
    
    def _get_template_version(self, config: TemplateConfig) -> str:
        """Get template version string"""
        return f"{config.style.value}_{config.layout.value}_{config.color_scheme.value}"
    
    async def _cache_rendered_template(
        self,
        rendered_template: RenderedTemplate,
        template_data: TemplateData
    ) -> None:
        """Cache rendered template"""
        cache_key = f"rendered_template:{template_data.user_persona.user_id}:{datetime.utcnow().date()}"
        cache_data = {
            "html_content": rendered_template.html_content,
            "text_content": rendered_template.text_content,
            "subject_line": rendered_template.subject_line,
            "template_version": rendered_template.template_version,
            "rendering_time": rendered_template.rendering_time
        }
        
        await self.cache.set(
            cache_key,
            json.dumps(cache_data, default=str),
            ttl=3600  # 1 hour cache
        )
    
    async def _render_fallback_template(
        self,
        template_data: TemplateData
    ) -> RenderedTemplate:
        """Render fallback template in case of errors"""
        fallback_config = TemplateConfig(
            style=TemplateStyle.MINIMAL,
            layout=LayoutType.SINGLE_COLUMN,
            color_scheme=ColorScheme.LIGHT,
            font_family="Arial, sans-serif",
            font_size="16px",
            header_style="simple",
            footer_style="minimal",
            content_density="normal",
            image_style="none",
            call_to_action_style="link",
            personalization_level="basic"
        )
        
        # Simple HTML fallback
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h1>📚 Your Reading Newsletter</h1>
            <p>Hello {template_data.user_persona.user_id},</p>
            <p>We have {len(template_data.content_items)} recommendations for you:</p>
            <ul>
        """
        
        for item in template_data.content_items:
            html_content += f"<li><strong>{item.title}</strong><br>{item.description}</li>"
        
        html_content += """
            </ul>
            <p>Happy reading!</p>
            <p><small><a href="{unsubscribe_url}">Unsubscribe</a></small></p>
        </body>
        </html>
        """.format(unsubscribe_url=template_data.unsubscribe_url)
        
        # Simple text fallback
        text_content = f"""
Your Reading Newsletter

Hello {template_data.user_persona.user_id},

We have {len(template_data.content_items)} recommendations for you:

"""
        for item in template_data.content_items:
            text_content += f"• {item.title}\n  {item.description}\n\n"
        
        text_content += f"""
Happy reading!

Unsubscribe: {template_data.unsubscribe_url}
"""
        
        return RenderedTemplate(
            html_content=html_content,
            text_content=text_content,
            subject_line=template_data.subject_line or "Your Reading Newsletter",
            preheader_text=template_data.preheader_text or "Personalized book recommendations",
            template_version="fallback",
            personalization_tokens={},
            rendering_time=0.1,
            template_config=fallback_config,
            metadata={"fallback": True}
        )
    
    async def _get_default_template_config(
        self,
        user_persona: UserPersona
    ) -> TemplateConfig:
        """Get default template configuration"""
        return TemplateConfig(
            style=TemplateStyle.NEWSLETTER,
            layout=LayoutType.SINGLE_COLUMN,
            color_scheme=ColorScheme.LIGHT,
            font_family="Inter, sans-serif",
            font_size="16px",
            header_style="modern",
            footer_style="minimal",
            content_density="normal",
            image_style="thumbnail",
            call_to_action_style="button",
            personalization_level="medium"
        )
    
    async def _analyze_template_engagement(
        self,
        user_id: str,
        engagement_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze template engagement patterns"""
        if not engagement_history:
            return {"no_data": True}
        
        # Group by template characteristics
        style_performance = {}
        layout_performance = {}
        color_performance = {}
        
        for record in engagement_history:
            template_version = record.get("template_version", "unknown")
            engagement_rate = record.get("engagement_rate", 0)
            
            # Parse template version
            parts = template_version.split("_")
            if len(parts) >= 3:
                style, layout, color = parts[:3]
                
                if style not in style_performance:
                    style_performance[style] = []
                style_performance[style].append(engagement_rate)
                
                if layout not in layout_performance:
                    layout_performance[layout] = []
                layout_performance[layout].append(engagement_rate)
                
                if color not in color_performance:
                    color_performance[color] = []
                color_performance[color].append(engagement_rate)
        
        # Calculate averages
        analysis = {
            "best_style": max(style_performance.items(), key=lambda x: sum(x[1])/len(x[1]))[0] if style_performance else "newsletter",
            "best_layout": max(layout_performance.items(), key=lambda x: sum(x[1])/len(x[1]))[0] if layout_performance else "single_column",
            "best_color": max(color_performance.items(), key=lambda x: sum(x[1])/len(x[1]))[0] if color_performance else "light",
            "total_data_points": len(engagement_history),
            "avg_engagement": sum(r.get("engagement_rate", 0) for r in engagement_history) / len(engagement_history)
        }
        
        return analysis
    
    async def _calculate_optimal_config(
        self,
        user_persona: UserPersona,
        engagement_analysis: Dict[str, Any]
    ) -> TemplateConfig:
        """Calculate optimal template configuration"""
        if engagement_analysis.get("no_data"):
            return await self._generate_config_from_persona(user_persona)
        
        # Use engagement analysis results
        try:
            style = TemplateStyle(engagement_analysis.get("best_style", "newsletter"))
        except ValueError:
            style = TemplateStyle.NEWSLETTER
        
        try:
            layout = LayoutType(engagement_analysis.get("best_layout", "single_column"))
        except ValueError:
            layout = LayoutType.SINGLE_COLUMN
        
        try:
            color_scheme = ColorScheme(engagement_analysis.get("best_color", "light"))
        except ValueError:
            color_scheme = ColorScheme.LIGHT
        
        return TemplateConfig(
            style=style,
            layout=layout,
            color_scheme=color_scheme,
            font_family="Inter, sans-serif",
            font_size="16px",
            header_style="modern",
            footer_style="minimal",
            content_density="normal",
            image_style="thumbnail",
            call_to_action_style="button",
            personalization_level="high"
        )
    
    async def _create_variant_config(
        self,
        base_config: TemplateConfig,
        test_parameter: str
    ) -> TemplateConfig:
        """Create variant configuration for A/B testing"""
        variant_config = TemplateConfig(**base_config.__dict__)
        
        if test_parameter == "style":
            # Test different style
            styles = [s for s in TemplateStyle if s != base_config.style]
            variant_config.style = styles[0] if styles else base_config.style
        
        elif test_parameter == "layout":
            # Test different layout
            layouts = [l for l in LayoutType if l != base_config.layout]
            variant_config.layout = layouts[0] if layouts else base_config.layout
        
        elif test_parameter == "color_scheme":
            # Test different color scheme
            colors = [c for c in ColorScheme if c != base_config.color_scheme]
            variant_config.color_scheme = colors[0] if colors else base_config.color_scheme
        
        elif test_parameter == "content_density":
            # Test different content density
            densities = ["sparse", "normal", "dense"]
            current_index = densities.index(base_config.content_density)
            next_index = (current_index + 1) % len(densities)
            variant_config.content_density = densities[next_index]
        
        return variant_config
    
    async def _generate_performance_insights(
        self,
        analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate insights from performance analysis"""
        insights = []
        
        if not analysis.get("config_performance"):
            insights.append("Insufficient data for meaningful insights")
            return insights
        
        # Find top performing configuration
        best_config = analysis.get("best_performing")
        if best_config:
            insights.append(f"Best performing template: {best_config['config_id']}")
            
            metrics = best_config["metrics"]
            if metrics["open_rate"] > 0.3:
                insights.append(f"Excellent open rate: {metrics['open_rate']:.1%}")
            if metrics["click_rate"] > 0.1:
                insights.append(f"Strong click rate: {metrics['click_rate']:.1%}")
        
        # Compare configurations
        config_performances = analysis["config_performance"]
        if len(config_performances) > 1:
            engagement_rates = [config["engagement_rate"] for config in config_performances.values()]
            max_rate = max(engagement_rates)
            min_rate = min(engagement_rates)
            
            if max_rate - min_rate > 0.1:
                insights.append(f"Significant performance difference: {(max_rate - min_rate):.1%}")
        
        return insights
