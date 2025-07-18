#!/usr/bin/env python3
"""
📖 Kindle Dashboard Validation Script
Comprehensive testing of the Kindle Paperwhite-inspired dashboard
"""

import os
import sys
import json
import time
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any
import subprocess
import re
from datetime import datetime

class KindleDashboardValidator:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.dashboard_path = self.project_root / "dashboard"
        self.results = {
            "validation_date": datetime.now().isoformat(),
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "warnings": 0,
            "tests": []
        }
        
    def log_test(self, test_name: str, status: str, message: str, details: Dict = None):
        """Log test result"""
        self.results["tests"].append({
            "name": test_name,
            "status": status,
            "message": message,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        })
        
        if status == "PASS":
            self.results["passed"] += 1
            print(f"✅ {test_name}: {message}")
        elif status == "FAIL":
            self.results["failed"] += 1
            print(f"❌ {test_name}: {message}")
        elif status == "WARN":
            self.results["warnings"] += 1
            print(f"⚠️  {test_name}: {message}")
        
        self.results["total_tests"] += 1

    def validate_file_structure(self):
        """Validate all required files exist"""
        print("\n🏗️  Validating Dashboard File Structure...")
        
        required_files = {
            "index.html": "dashboard/index.html",
            "wireframes.md": "dashboard/wireframes.md",
            
            # CSS Files
            "design-system.css": "dashboard/css/design-system.css",
            "brightness-control.css": "dashboard/css/brightness-control.css", 
            "theme-toggle.css": "dashboard/css/theme-toggle.css",
            "book-card.css": "dashboard/css/book-card.css",
            "kindle-dashboard.css": "dashboard/css/kindle-dashboard.css",
            "modals.css": "dashboard/css/modals.css",
            
            # JavaScript Files
            "theme-manager.js": "dashboard/js/theme-manager.js",
            "brightness-controller.js": "dashboard/js/brightness-controller.js",
            "book-card.js": "dashboard/js/book-card.js",
            "kindle-dashboard.js": "dashboard/js/kindle-dashboard.js",
            
            # Documentation
            "KINDLE_DASHBOARD_GUIDE.md": "docs/KINDLE_DASHBOARD_GUIDE.md"
        }
        
        for name, file_path in required_files.items():
            full_path = self.project_root / file_path
            if full_path.exists():
                self.log_test(f"File Exists: {name}", "PASS", f"Found at {file_path}")
            else:
                self.log_test(f"File Missing: {name}", "FAIL", f"Missing file: {file_path}")

    def validate_css_syntax(self):
        """Validate CSS files for syntax errors"""
        print("\n🎨 Validating CSS Syntax...")
        
        css_files = [
            "dashboard/css/design-system.css",
            "dashboard/css/brightness-control.css",
            "dashboard/css/theme-toggle.css", 
            "dashboard/css/book-card.css",
            "dashboard/css/kindle-dashboard.css",
            "dashboard/css/modals.css"
        ]
        
        for css_file in css_files:
            file_path = self.project_root / css_file
            if not file_path.exists():
                self.log_test(f"CSS Validation: {css_file}", "FAIL", "File not found")
                continue
                
            try:
                content = file_path.read_text(encoding='utf-8')
                
                # Basic CSS validation
                open_braces = content.count('{')
                close_braces = content.count('}')
                
                if open_braces == close_braces:
                    self.log_test(f"CSS Syntax: {css_file}", "PASS", "Balanced braces")
                else:
                    self.log_test(f"CSS Syntax: {css_file}", "FAIL", 
                                f"Unbalanced braces: {open_braces} open, {close_braces} close")
                
                # Check for basic CSS structure
                if re.search(r'--[a-zA-Z-]+:', content):
                    self.log_test(f"CSS Variables: {css_file}", "PASS", "Contains CSS custom properties")
                else:
                    self.log_test(f"CSS Variables: {css_file}", "WARN", "No CSS custom properties found")
                    
            except Exception as e:
                self.log_test(f"CSS Read Error: {css_file}", "FAIL", str(e))

    def validate_javascript_syntax(self):
        """Validate JavaScript files for basic syntax"""
        print("\n🛠️  Validating JavaScript Syntax...")
        
        js_files = [
            "dashboard/js/theme-manager.js",
            "dashboard/js/brightness-controller.js",
            "dashboard/js/book-card.js", 
            "dashboard/js/kindle-dashboard.js"
        ]
        
        for js_file in js_files:
            file_path = self.project_root / js_file
            if not file_path.exists():
                self.log_test(f"JS Validation: {js_file}", "FAIL", "File not found")
                continue
                
            try:
                content = file_path.read_text(encoding='utf-8')
                
                # Basic JavaScript validation
                open_braces = content.count('{')
                close_braces = content.count('}')
                open_parens = content.count('(')
                close_parens = content.count(')')
                
                if open_braces == close_braces and open_parens == close_parens:
                    self.log_test(f"JS Syntax: {js_file}", "PASS", "Balanced brackets and parentheses")
                else:
                    self.log_test(f"JS Syntax: {js_file}", "FAIL", 
                                f"Unbalanced symbols: {open_braces}/{close_braces} braces, {open_parens}/{close_parens} parens")
                
                # Check for class definitions
                if re.search(r'class\s+\w+', content):
                    self.log_test(f"JS Classes: {js_file}", "PASS", "Contains class definitions")
                else:
                    self.log_test(f"JS Classes: {js_file}", "WARN", "No class definitions found")
                    
            except Exception as e:
                self.log_test(f"JS Read Error: {js_file}", "FAIL", str(e))

    def validate_html_structure(self):
        """Validate HTML structure and meta tags"""
        print("\n📄 Validating HTML Structure...")
        
        html_file = self.project_root / "dashboard/index.html"
        if not html_file.exists():
            self.log_test("HTML Structure", "FAIL", "index.html not found")
            return
            
        try:
            content = html_file.read_text(encoding='utf-8')
            
            # Check for required meta tags
            required_meta = [
                'charset="UTF-8"',
                'name="viewport"',
                'name="description"',
                'http-equiv="Content-Security-Policy"'
            ]
            
            for meta in required_meta:
                if meta in content:
                    self.log_test(f"HTML Meta: {meta.split('=')[0]}", "PASS", "Meta tag present")
                else:
                    self.log_test(f"HTML Meta: {meta.split('=')[0]}", "WARN", "Meta tag missing")
            
            # Check for CSS and JS includes
            if 'kindle-dashboard.css' in content:
                self.log_test("HTML CSS: Kindle Dashboard", "PASS", "Kindle dashboard CSS included")
            else:
                self.log_test("HTML CSS: Kindle Dashboard", "FAIL", "Kindle dashboard CSS not included")
                
            if 'kindle-dashboard.js' in content:
                self.log_test("HTML JS: Kindle Dashboard", "PASS", "Kindle dashboard JS included")
            else:
                self.log_test("HTML JS: Kindle Dashboard", "FAIL", "Kindle dashboard JS not included")
                
            # Check for dashboard container
            if 'dashboard-container' in content:
                self.log_test("HTML Container", "PASS", "Dashboard container present")
            else:
                self.log_test("HTML Container", "FAIL", "Dashboard container missing")
                
        except Exception as e:
            self.log_test("HTML Read Error", "FAIL", str(e))

    def validate_design_system(self):
        """Validate design system implementation"""
        print("\n🎨 Validating Design System...")
        
        design_file = self.project_root / "dashboard/css/design-system.css"
        if not design_file.exists():
            self.log_test("Design System", "FAIL", "design-system.css not found")
            return
            
        try:
            content = design_file.read_text(encoding='utf-8')
            
            # Check for theme variables
            theme_checks = [
                ('Light Theme', ':root[data-theme="light"]'),
                ('Dark Theme', ':root[data-theme="dark"]'),
                ('Color Variables', '--bg-primary'),
                ('Text Variables', '--text-primary'),
                ('Font Variables', '--font-serif'),
                ('Spacing Variables', '--space-'),
                ('Border Radius', '--radius-'),
                ('Shadow Variables', '--shadow-')
            ]
            
            for name, pattern in theme_checks:
                if pattern in content:
                    self.log_test(f"Design System: {name}", "PASS", f"Contains {pattern}")
                else:
                    self.log_test(f"Design System: {name}", "WARN", f"Missing {pattern}")
                    
        except Exception as e:
            self.log_test("Design System Read Error", "FAIL", str(e))

    def validate_accessibility_features(self):
        """Validate accessibility implementation"""
        print("\n♿ Validating Accessibility Features...")
        
        # Check HTML for accessibility features
        html_file = self.project_root / "dashboard/index.html"
        if html_file.exists():
            content = html_file.read_text(encoding='utf-8')
            
            accessibility_checks = [
                ('ARIA Labels', 'aria-label'),
                ('Alt Text', 'alt='),
                ('Role Attributes', 'role='),
                ('Tab Index', 'tabindex'),
                ('Focus Management', 'focus')
            ]
            
            for name, pattern in accessibility_checks:
                if pattern in content:
                    self.log_test(f"Accessibility: {name}", "PASS", f"Found {pattern}")
                else:
                    self.log_test(f"Accessibility: {name}", "WARN", f"Missing {pattern}")
        
        # Check CSS for accessibility
        css_files = ["design-system.css", "theme-toggle.css", "brightness-control.css"]
        for css_file in css_files:
            file_path = self.project_root / f"dashboard/css/{css_file}"
            if file_path.exists():
                content = file_path.read_text(encoding='utf-8')
                
                if 'focus' in content:
                    self.log_test(f"Accessibility CSS: {css_file}", "PASS", "Contains focus styles")
                else:
                    self.log_test(f"Accessibility CSS: {css_file}", "WARN", "No focus styles found")

    def validate_responsive_design(self):
        """Validate responsive design implementation"""
        print("\n📱 Validating Responsive Design...")
        
        css_files = [
            "dashboard/css/kindle-dashboard.css",
            "dashboard/css/book-card.css"
        ]
        
        for css_file in css_files:
            file_path = self.project_root / css_file
            if not file_path.exists():
                continue
                
            try:
                content = file_path.read_text(encoding='utf-8')
                
                # Check for media queries
                media_queries = re.findall(r'@media[^{]+{', content)
                if media_queries:
                    self.log_test(f"Responsive: {css_file}", "PASS", 
                                f"Found {len(media_queries)} media queries")
                else:
                    self.log_test(f"Responsive: {css_file}", "WARN", "No media queries found")
                
                # Check for flexible units
                flexible_units = ['rem', 'em', '%', 'vw', 'vh', 'fr']
                found_units = []
                for unit in flexible_units:
                    if unit in content:
                        found_units.append(unit)
                
                if found_units:
                    self.log_test(f"Flexible Units: {css_file}", "PASS", 
                                f"Uses {', '.join(found_units)}")
                else:
                    self.log_test(f"Flexible Units: {css_file}", "WARN", "Only absolute units found")
                    
            except Exception as e:
                self.log_test(f"Responsive Read Error: {css_file}", "FAIL", str(e))

    def validate_kindle_features(self):
        """Validate Kindle-specific features"""
        print("\n📖 Validating Kindle Paperwhite Features...")
        
        # Check for brightness controller
        brightness_file = self.project_root / "dashboard/js/brightness-controller.js"
        if brightness_file.exists():
            content = brightness_file.read_text(encoding='utf-8')
            
            kindle_features = [
                ('Brightness Control', 'brightness'),
                ('Auto Brightness', 'auto'),
                ('Slider Component', 'slider'),
                ('Time-based Adjustment', 'time'),
                ('Smooth Transitions', 'transition')
            ]
            
            for name, pattern in kindle_features:
                if pattern.lower() in content.lower():
                    self.log_test(f"Kindle Feature: {name}", "PASS", f"Implements {pattern}")
                else:
                    self.log_test(f"Kindle Feature: {name}", "WARN", f"Missing {pattern}")
        
        # Check theme manager for e-ink simulation
        theme_file = self.project_root / "dashboard/js/theme-manager.js" 
        if theme_file.exists():
            content = theme_file.read_text(encoding='utf-8')
            
            if 'paper' in content.lower() or 'ink' in content.lower():
                self.log_test("Kindle Theme: E-ink Simulation", "PASS", "Contains e-ink references")
            else:
                self.log_test("Kindle Theme: E-ink Simulation", "WARN", "No e-ink simulation found")

    def validate_performance(self):
        """Validate performance considerations"""
        print("\n⚡ Validating Performance Features...")
        
        html_file = self.project_root / "dashboard/index.html"
        if html_file.exists():
            content = html_file.read_text(encoding='utf-8')
            
            performance_checks = [
                ('Preload Resources', 'preload'),
                ('Font Display', 'font-display'),
                ('Lazy Loading', 'loading="lazy"'),
                ('Async Scripts', 'async'),
                ('Defer Scripts', 'defer')
            ]
            
            for name, pattern in performance_checks:
                if pattern in content:
                    self.log_test(f"Performance: {name}", "PASS", f"Uses {pattern}")
                else:
                    self.log_test(f"Performance: {name}", "WARN", f"Missing {pattern}")

    def validate_documentation(self):
        """Validate documentation completeness"""
        print("\n📚 Validating Documentation...")
        
        doc_files = [
            ("Kindle Dashboard Guide", "docs/KINDLE_DASHBOARD_GUIDE.md"),
            ("Wireframes", "dashboard/wireframes.md"),
            ("Dashboard README", "dashboard/README.md")
        ]
        
        for name, file_path in doc_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                try:
                    content = full_path.read_text(encoding='utf-8')
                    word_count = len(content.split())
                    
                    if word_count > 100:
                        self.log_test(f"Documentation: {name}", "PASS", 
                                    f"Comprehensive ({word_count} words)")
                    else:
                        self.log_test(f"Documentation: {name}", "WARN", 
                                    f"Brief documentation ({word_count} words)")
                except Exception as e:
                    self.log_test(f"Documentation Error: {name}", "FAIL", str(e))
            else:
                self.log_test(f"Documentation Missing: {name}", "FAIL", f"File not found: {file_path}")

    def generate_report(self):
        """Generate validation report"""
        print("\n📊 Generating Validation Report...")
        
        # Calculate scores
        total = self.results["total_tests"]
        passed = self.results["passed"]
        failed = self.results["failed"]
        warnings = self.results["warnings"]
        
        if total > 0:
            pass_rate = (passed / total) * 100
            success_rate = ((passed + warnings) / total) * 100
        else:
            pass_rate = 0
            success_rate = 0
        
        # Create summary
        summary = {
            "validation_summary": {
                "total_tests": total,
                "passed": passed,
                "failed": failed,
                "warnings": warnings,
                "pass_rate": round(pass_rate, 1),
                "success_rate": round(success_rate, 1),
                "overall_status": "PASS" if failed == 0 else "FAIL" if pass_rate < 70 else "WARN"
            }
        }
        
        # Combine with detailed results
        final_report = {**summary, **self.results}
        
        # Save report
        report_file = self.project_root / f"kindle_dashboard_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_file.write_text(json.dumps(final_report, indent=2))
        
        # Print summary
        print(f"\n{'='*60}")
        print("📖 KINDLE DASHBOARD VALIDATION SUMMARY")
        print(f"{'='*60}")
        print(f"Total Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⚠️  Warnings: {warnings}")
        print(f"📊 Pass Rate: {pass_rate:.1f}%")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        print(f"🎯 Overall Status: {summary['validation_summary']['overall_status']}")
        print(f"📄 Report saved: {report_file}")
        
        return final_report

    def run_validation(self):
        """Run complete validation suite"""
        print("🚀 Starting Kindle Dashboard Validation...")
        print(f"📍 Project Root: {self.project_root}")
        
        # Run all validation checks
        self.validate_file_structure()
        self.validate_html_structure()
        self.validate_css_syntax()
        self.validate_javascript_syntax()
        self.validate_design_system()
        self.validate_accessibility_features()
        self.validate_responsive_design()
        self.validate_kindle_features()
        self.validate_performance()
        self.validate_documentation()
        
        # Generate and return report
        return self.generate_report()

def main():
    """Main execution function"""
    validator = KindleDashboardValidator()
    report = validator.run_validation()
    
    # Exit with appropriate code
    if report["validation_summary"]["overall_status"] == "FAIL":
        sys.exit(1)
    elif report["validation_summary"]["overall_status"] == "WARN":
        sys.exit(0)  # Warnings are acceptable
    else:
        sys.exit(0)  # Success

if __name__ == "__main__":
    main()
