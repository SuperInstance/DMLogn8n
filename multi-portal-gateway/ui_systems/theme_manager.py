"""
Advanced Theme Manager for DMLogn8n Platform
Dynamic theming and personalization with light/dark modes and custom themes
"""

import asyncio
import json
import colorsys
from datetime import datetime, time
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import logging

class ThemeType(Enum):
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"
    CUSTOM = "custom"
    HIGH_CONTRAST = "high_contrast"
    SEPIA = "sepia"
    BLUE_LIGHT = "blue_light"

class ColorScheme(Enum):
    DEFAULT = "default"
    BLUE = "blue"
    GREEN = "green"
    PURPLE = "purple"
    RED = "red"
    ORANGE = "orange"
    TEAL = "teal"
    INDIGO = "indigo"
    PINK = "pink"
    GRAY = "gray"

class FontFamily(Enum):
    SYSTEM = "system"
    SANS_SERIF = "sans_serif"
    SERIF = "serif"
    MONOSPACE = "monospace"
    DISPLAY = "display"

@dataclass
class Color:
    hex_value: str
    rgb: Tuple[int, int, int]
    hsl: Tuple[float, float, float]
    name: str

    @classmethod
    def from_hex(cls, hex_value: str, name: str = ""):
        """Create Color from hex value"""
        hex_value = hex_value.lstrip('#')
        rgb = tuple(int(hex_value[i:i+2], 16) for i in (0, 2, 4))
        hsl = cls._rgb_to_hsl(rgb)
        return cls(hex_value, rgb, hsl, name)

    @staticmethod
    def _rgb_to_hsl(rgb: Tuple[int, int, int]) -> Tuple[float, float, float]:
        """Convert RGB to HSL"""
        r, g, b = [x / 255.0 for x in rgb]
        max_val = max(r, g, b)
        min_val = min(r, g, b)
        l = (max_val + min_val) / 2.0

        if max_val == min_val:
            h = s = 0.0
        else:
            d = max_val - min_val
            s = d / (2.0 - max_val - min_val) if l > 0.5 else d / (max_val + min_val)

            if max_val == r:
                h = (g - b) / d + (6.0 if g < b else 0)
            elif max_val == g:
                h = (b - r) / d + 2.0
            else:
                h = (r - g) / d + 4.0
            h /= 6.0

        return (h * 360, s * 100, l * 100)

    def adjust_brightness(self, factor: float) -> 'Color':
        """Adjust color brightness"""
        h, s, l = self.hsl
        new_l = max(0, min(100, l * factor))
        new_rgb = self._hsl_to_rgb((h / 360, s / 100, new_l / 100))
        new_hex = '#{:02x}{:02x}{:02x}'.format(*new_rgb)
        return Color.from_hex(new_hex, f"{self.name}_adjusted")

    @staticmethod
    def _hsl_to_rgb(hsl: Tuple[float, float, float]) -> Tuple[int, int, int]:
        """Convert HSL to RGB"""
        h, s, l = hsl
        c = (1 - abs(2 * l - 1)) * s
        x = c * (1 - abs((h * 6) % 2 - 1))
        m = l - c / 2

        if 0 <= h < 1/6:
            r, g, b = c, x, 0
        elif 1/6 <= h < 2/6:
            r, g, b = x, c, 0
        elif 2/6 <= h < 3/6:
            r, g, b = 0, c, x
        elif 3/6 <= h < 4/6:
            r, g, b = 0, x, c
        elif 4/6 <= h < 5/6:
            r, g, b = x, 0, c
        else:
            r, g, b = c, 0, x

        return (int((r + m) * 255), int((g + m) * 255), int((b + m) * 255))

@dataclass
class Theme:
    theme_id: str
    name: str
    theme_type: ThemeType
    color_scheme: ColorScheme
    colors: Dict[str, Color]
    fonts: Dict[str, FontFamily]
    font_sizes: Dict[str, int]
    spacing: Dict[str, int]
    borders: Dict[str, Dict[str, Any]]
    shadows: Dict[str, str]
    animations: Dict[str, Dict[str, Any]]
    custom_css: str
    metadata: Dict[str, Any]

@dataclass
class ThemePreferences:
    user_id: str
    preferred_theme_type: ThemeType
    preferred_color_scheme: ColorScheme
    auto_switch_enabled: bool
    light_theme_start: time
    dark_theme_start: time
    font_size_multiplier: float
    high_contrast_enabled: bool
    blue_light_filter_enabled: bool
    custom_colors: Dict[str, str]
    saved_themes: List[str]

class ThemeManager:
    """Advanced theme management system"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

        # Theme storage
        self.themes: Dict[str, Theme] = {}
        self.current_themes: Dict[str, str] = {}  # user_id -> theme_id
        self.theme_preferences: Dict[str, ThemePreferences] = {}

        # Color system
        self.color_generator = ColorGenerator()
        self.color_palette_generator = ColorPaletteGenerator()

        # Theme switching
        self.auto_switch_task: Optional[asyncio.Task] = None
        self.theme_transition_active = False

        # Performance optimization
        self.theme_cache = {}
        self.compiled_themes: Dict[str, Dict[str, Any]] = {}

        self._initialize_default_themes()
        self._start_auto_theme_switcher()

    def _initialize_default_themes(self):
        """Initialize default themes"""
        default_themes = [
            self._create_light_theme(),
            self._create_dark_theme(),
            self._create_high_contrast_theme(),
            self._create_sepia_theme(),
            self._create_blue_light_theme()
        ]

        # Add color scheme variations
        base_schemes = [ColorScheme.BLUE, ColorScheme.GREEN, ColorScheme.PURPLE,
                       ColorScheme.RED, ColorScheme.ORANGE, ColorScheme.TEAL,
                       ColorScheme.INDIGO, ColorScheme.PINK]

        for scheme in base_schemes:
            # Light variation
            light_theme = self._create_color_scheme_theme(scheme, ThemeType.LIGHT)
            default_themes.append(light_theme)

            # Dark variation
            dark_theme = self._create_color_scheme_theme(scheme, ThemeType.DARK)
            default_themes.append(dark_theme)

        for theme in default_themes:
            self.themes[theme.theme_id] = theme

    def _create_light_theme(self) -> Theme:
        """Create default light theme"""
        colors = {
            'primary': Color.from_hex('#007bff', 'primary'),
            'secondary': Color.from_hex('#6c757d', 'secondary'),
            'success': Color.from_hex('#28a745', 'success'),
            'danger': Color.from_hex('#dc3545', 'danger'),
            'warning': Color.from_hex('#ffc107', 'warning'),
            'info': Color.from_hex('#17a2b8', 'info'),
            'background': Color.from_hex('#ffffff', 'background'),
            'surface': Color.from_hex('#f8f9fa', 'surface'),
            'text_primary': Color.from_hex('#212529', 'text_primary'),
            'text_secondary': Color.from_hex('#6c757d', 'text_secondary'),
            'border': Color.from_hex('#dee2e6', 'border'),
            'shadow': Color.from_hex('#000000', 'shadow'),
            'accent': Color.from_hex('#6610f2', 'accent')
        }

        return Theme(
            theme_id='light_default',
            name='Light Default',
            theme_type=ThemeType.LIGHT,
            color_scheme=ColorScheme.DEFAULT,
            colors=colors,
            fonts={
                'primary': FontFamily.SANS_SERIF,
                'secondary': FontFamily.SANS_SERIF,
                'monospace': FontFamily.MONOSPACE,
                'display': FontFamily.DISPLAY
            },
            font_sizes={
                'xs': 12,
                'sm': 14,
                'base': 16,
                'lg': 18,
                'xl': 20,
                '2xl': 24,
                '3xl': 30,
                '4xl': 36,
                '5xl': 48
            },
            spacing={
                'xs': 4,
                'sm': 8,
                'md': 16,
                'lg': 24,
                'xl': 32,
                '2xl': 48,
                '3xl': 64
            },
            borders={
                'radius_sm': 4,
                'radius_md': 8,
                'radius_lg': 12,
                'radius_xl': 16,
                'width_thin': 1,
                'width_medium': 2,
                'width_thick': 4
            },
            shadows={
                'sm': '0 1px 2px rgba(0, 0, 0, 0.05)',
                'md': '0 4px 6px rgba(0, 0, 0, 0.07)',
                'lg': '0 10px 15px rgba(0, 0, 0, 0.1)',
                'xl': '0 20px 25px rgba(0, 0, 0, 0.1)'
            },
            animations={
                'duration_fast': 150,
                'duration_normal': 300,
                'duration_slow': 500,
                'easing_default': 'cubic-bezier(0.4, 0, 0.2, 1)'
            },
            custom_css='',
            metadata={
                'created_at': datetime.now().isoformat(),
                'author': 'system',
                'version': '1.0'
            }
        )

    def _create_dark_theme(self) -> Theme:
        """Create default dark theme"""
        colors = {
            'primary': Color.from_hex('#0d6efd', 'primary'),
            'secondary': Color.from_hex('#6c757d', 'secondary'),
            'success': Color.from_hex('#198754', 'success'),
            'danger': Color.from_hex('#dc3545', 'danger'),
            'warning': Color.from_hex('#ffc107', 'warning'),
            'info': Color.from_hex('#0dcaf0', 'info'),
            'background': Color.from_hex('#121212', 'background'),
            'surface': Color.from_hex('#1e1e1e', 'surface'),
            'text_primary': Color.from_hex('#ffffff', 'text_primary'),
            'text_secondary': Color.from_hex('#adb5bd', 'text_secondary'),
            'border': Color.from_hex('#495057', 'border'),
            'shadow': Color.from_hex('#000000', 'shadow'),
            'accent': Color.from_hex('#7c3aed', 'accent')
        }

        base_theme = self._create_light_theme()
        return Theme(
            theme_id='dark_default',
            name='Dark Default',
            theme_type=ThemeType.DARK,
            color_scheme=ColorScheme.DEFAULT,
            colors=colors,
            fonts=base_theme.fonts,
            font_sizes=base_theme.font_sizes,
            spacing=base_theme.spacing,
            borders=base_theme.borders,
            shadows={
                'sm': '0 1px 2px rgba(0, 0, 0, 0.3)',
                'md': '0 4px 6px rgba(0, 0, 0, 0.4)',
                'lg': '0 10px 15px rgba(0, 0, 0, 0.5)',
                'xl': '0 20px 25px rgba(0, 0, 0, 0.5)'
            },
            animations=base_theme.animations,
            custom_css='',
            metadata={
                'created_at': datetime.now().isoformat(),
                'author': 'system',
                'version': '1.0'
            }
        )

    def _create_high_contrast_theme(self) -> Theme:
        """Create high contrast theme"""
        colors = {
            'primary': Color.from_hex('#0000ff', 'primary'),
            'secondary': Color.from_hex('#ffffff', 'secondary'),
            'success': Color.from_hex('#00ff00', 'success'),
            'danger': Color.from_hex('#ff0000', 'danger'),
            'warning': Color.from_hex('#ffff00', 'warning'),
            'info': Color.from_hex('#00ffff', 'info'),
            'background': Color.from_hex('#000000', 'background'),
            'surface': Color.from_hex('#1a1a1a', 'surface'),
            'text_primary': Color.from_hex('#ffffff', 'text_primary'),
            'text_secondary': Color.from_hex('#cccccc', 'text_secondary'),
            'border': Color.from_hex('#ffffff', 'border'),
            'shadow': Color.from_hex('#808080', 'shadow'),
            'accent': Color.from_hex('#ff00ff', 'accent')
        }

        base_theme = self._create_light_theme()
        return Theme(
            theme_id='high_contrast',
            name='High Contrast',
            theme_type=ThemeType.HIGH_CONTRAST,
            color_scheme=ColorScheme.DEFAULT,
            colors=colors,
            fonts=base_theme.fonts,
            font_sizes={k: v + 2 for k, v in base_theme.font_sizes.items()},  # Larger fonts
            spacing=base_theme.spacing,
            borders={**base_theme.borders, 'width_medium': 3},  # Thicker borders
            shadows=base_theme.shadows,
            animations=base_theme.animations,
            custom_css='',
            metadata={
                'created_at': datetime.now().isoformat(),
                'author': 'system',
                'version': '1.0',
                'accessibility': True
            }
        )

    def _create_sepia_theme(self) -> Theme:
        """Create sepia theme"""
        colors = {
            'primary': Color.from_hex('#8b7355', 'primary'),
            'secondary': Color.from_hex('#a0826d', 'secondary'),
            'success': Color.from_hex('#6b8e23', 'success'),
            'danger': Color.from_hex('#cd5c5c', 'danger'),
            'warning': Color.from_hex('#daa520', 'warning'),
            'info': Color.from_hex('#4682b4', 'info'),
            'background': Color.from_hex('#f4ecd8', 'background'),
            'surface': Color.from_hex('#f5e6d3', 'surface'),
            'text_primary': Color.from_hex('#5d4037', 'text_primary'),
            'text_secondary': Color.from_hex('#8d6e63', 'text_secondary'),
            'border': Color.from_hex('#d7ccc8', 'border'),
            'shadow': Color.from_hex('#3e2723', 'shadow'),
            'accent': Color.from_hex('#ff8f00', 'accent')
        }

        base_theme = self._create_light_theme()
        return Theme(
            theme_id='sepia',
            name='Sepia',
            theme_type=ThemeType.SEPIA,
            color_scheme=ColorScheme.DEFAULT,
            colors=colors,
            fonts=base_theme.fonts,
            font_sizes=base_theme.font_sizes,
            spacing=base_theme.spacing,
            borders=base_theme.borders,
            shadows=base_theme.shadows,
            animations=base_theme.animations,
            custom_css='',
            metadata={
                'created_at': datetime.now().isoformat(),
                'author': 'system',
                'version': '1.0'
            }
        )

    def _create_blue_light_theme(self) -> Theme:
        """Create blue light filter theme"""
        colors = {
            'primary': Color.from_hex('#0066cc', 'primary'),
            'secondary': Color.from_hex('#666666', 'secondary'),
            'success': Color.from_hex('#228b22', 'success'),
            'danger': Color.from_hex('#cc6666', 'danger'),
            'warning': Color.from_hex('#cc9966', 'warning'),
            'info': Color.from_hex('#6699cc', 'info'),
            'background': Color.from_hex('#f5f5dc', 'background'),
            'surface': Color.from_hex('#fafaf0', 'surface'),
            'text_primary': Color.from_hex('#333333', 'text_primary'),
            'text_secondary': Color.from_hex('#666666', 'text_secondary'),
            'border': Color.from_hex('#cccccc', 'border'),
            'shadow': Color.from_hex('#999999', 'shadow'),
            'accent': Color.from_hex('#9966cc', 'accent')
        }

        base_theme = self._create_light_theme()
        return Theme(
            theme_id='blue_light',
            name='Blue Light Filter',
            theme_type=ThemeType.BLUE_LIGHT,
            color_scheme=ColorScheme.DEFAULT,
            colors=colors,
            fonts=base_theme.fonts,
            font_sizes=base_theme.font_sizes,
            spacing=base_theme.spacing,
            borders=base_theme.borders,
            shadows=base_theme.shadows,
            animations=base_theme.animations,
            custom_css='',
            metadata={
                'created_at': datetime.now().isoformat(),
                'author': 'system',
                'version': '1.0',
                'eye_care': True
            }
        )

    def _create_color_scheme_theme(self, color_scheme: ColorScheme, theme_type: ThemeType) -> Theme:
        """Create theme based on color scheme"""
        # Generate color palette
        primary_color = self.color_palette_generator.get_primary_color(color_scheme)
        color_palette = self.color_palette_generator.generate_palette(primary_color)

        # Adjust for theme type
        if theme_type == ThemeType.DARK:
            background_color = Color.from_hex('#1a1a1a', 'background')
            text_color = Color.from_hex('#ffffff', 'text_primary')
            surface_color = Color.from_hex('#2d2d2d', 'surface')
        else:
            background_color = Color.from_hex('#ffffff', 'background')
            text_color = Color.from_hex('#333333', 'text_primary')
            surface_color = Color.from_hex('#f8f9fa', 'surface')

        colors = {
            'primary': color_palette['primary'],
            'secondary': color_palette['secondary'],
            'success': Color.from_hex('#28a745', 'success'),
            'danger': Color.from_hex('#dc3545', 'danger'),
            'warning': Color.from_hex('#ffc107', 'warning'),
            'info': Color.from_hex('#17a2b8', 'info'),
            'background': background_color,
            'surface': surface_color,
            'text_primary': text_color,
            'text_secondary': color_palette['text_secondary'],
            'border': color_palette['border'],
            'shadow': Color.from_hex('#000000', 'shadow'),
            'accent': color_palette['accent']
        }

        base_theme = self._create_light_theme()
        return Theme(
            theme_id=f'{theme_type.value}_{color_scheme.value}',
            name=f'{color_scheme.value.title()} {theme_type.value.title()}',
            theme_type=theme_type,
            color_scheme=color_scheme,
            colors=colors,
            fonts=base_theme.fonts,
            font_sizes=base_theme.font_sizes,
            spacing=base_theme.spacing,
            borders=base_theme.borders,
            shadows=base_theme.shadows,
            animations=base_theme.animations,
            custom_css='',
            metadata={
                'created_at': datetime.now().isoformat(),
                'author': 'system',
                'version': '1.0'
            }
        )

    def _start_auto_theme_switcher(self):
        """Start automatic theme switching based on time"""
        self.auto_switch_task = asyncio.create_task(self._auto_theme_switch_loop())

    async def _auto_theme_switch_loop(self):
        """Auto theme switching loop"""
        while True:
            try:
                current_time = datetime.now().time()

                for user_id, preferences in self.theme_preferences.items():
                    if preferences.auto_switch_enabled:
                        # Check if we need to switch themes
                        current_theme_id = self.current_themes.get(user_id)
                        current_theme = self.themes.get(current_theme_id)

                        if current_theme and current_theme.theme_type != ThemeType.AUTO:
                            continue

                        # Determine which theme should be active
                        if self._should_be_dark_theme(current_time, preferences):
                            target_theme_type = ThemeType.DARK
                        else:
                            target_theme_type = ThemeType.LIGHT

                        # Find theme ID
                        target_theme_id = self._find_theme_id_for_type(
                            target_theme_type, preferences.preferred_color_scheme
                        )

                        # Switch if needed
                        if target_theme_id != current_theme_id:
                            await self.apply_theme(user_id, target_theme_id)

                # Check every minute
                await asyncio.sleep(60)

            except Exception as e:
                self.logger.error(f"Error in auto theme switcher: {e}")
                await asyncio.sleep(60)

    def _should_be_dark_theme(self, current_time: time, preferences: ThemePreferences) -> bool:
        """Determine if dark theme should be active based on time"""
        if preferences.light_theme_start <= preferences.dark_theme_start:
            # Time range doesn't cross midnight
            return preferences.dark_theme_start <= current_time < preferences.light_theme_start
        else:
            # Time range crosses midnight
            return current_time >= preferences.dark_theme_start or current_time < preferences.light_theme_start

    def _find_theme_id_for_type(self, theme_type: ThemeType, color_scheme: ColorScheme) -> str:
        """Find theme ID for given type and color scheme"""
        target_id = f'{theme_type.value}_{color_scheme.value}'
        if target_id in self.themes:
            return target_id

        # Fallback to default theme of type
        fallback_id = f'{theme_type.value}_default'
        if fallback_id in self.themes:
            return fallback_id

        # Final fallback
        return 'light_default'

    async def create_theme_preferences(self, user_id: str, preference_data: Dict[str, Any]) -> ThemePreferences:
        """Create theme preferences for user"""
        preferences = ThemePreferences(
            user_id=user_id,
            preferred_theme_type=ThemeType(preference_data.get('preferred_theme_type', 'light')),
            preferred_color_scheme=ColorScheme(preference_data.get('preferred_color_scheme', 'default')),
            auto_switch_enabled=preference_data.get('auto_switch_enabled', False),
            light_theme_start=time.fromisoformat(preference_data.get('light_theme_start', '08:00')),
            dark_theme_start=time.fromisoformat(preference_data.get('dark_theme_start', '20:00')),
            font_size_multiplier=preference_data.get('font_size_multiplier', 1.0),
            high_contrast_enabled=preference_data.get('high_contrast_enabled', False),
            blue_light_filter_enabled=preference_data.get('blue_light_filter_enabled', False),
            custom_colors=preference_data.get('custom_colors', {}),
            saved_themes=preference_data.get('saved_themes', [])
        )

        self.theme_preferences[user_id] = preferences

        # Apply initial theme
        initial_theme_id = self._find_theme_id_for_type(
            preferences.preferred_theme_type,
            preferences.preferred_color_scheme
        )
        await self.apply_theme(user_id, initial_theme_id)

        self.logger.info(f"Created theme preferences for user {user_id}")
        return preferences

    async def apply_theme(self, user_id: str, theme_id: str, transition: bool = True) -> bool:
        """Apply theme to user interface"""
        if theme_id not in self.themes:
            self.logger.error(f"Theme {theme_id} not found")
            return False

        theme = self.themes[theme_id]
        preferences = self.theme_preferences.get(user_id)

        # Apply user customizations
        customized_theme = await self._apply_user_customizations(theme, preferences)

        # Compile theme for performance
        compiled_theme = self._compile_theme(customized_theme)
        self.compiled_themes[user_id] = compiled_theme

        # Apply with transition
        if transition and user_id in self.current_themes:
            await self._transition_theme(user_id, theme_id)
        else:
            await self._apply_theme_immediately(user_id, compiled_theme)

        self.current_themes[user_id] = theme_id
        self.logger.info(f"Applied theme {theme_id} to user {user_id}")
        return True

    async def _apply_user_customizations(self, theme: Theme, preferences: Optional[ThemePreferences]) -> Theme:
        """Apply user customizations to theme"""
        if not preferences:
            return theme

        # Create a copy of the theme
        customized_theme = Theme(
            theme_id=theme.theme_id,
            name=theme.name,
            theme_type=theme.theme_type,
            color_scheme=theme.color_scheme,
            colors=theme.colors.copy(),
            fonts=theme.fonts.copy(),
            font_sizes=theme.font_sizes.copy(),
            spacing=theme.spacing.copy(),
            borders=theme.borders.copy(),
            shadows=theme.shadows.copy(),
            animations=theme.animations.copy(),
            custom_css=theme.custom_css,
            metadata=theme.metadata.copy()
        )

        # Apply font size multiplier
        if preferences.font_size_multiplier != 1.0:
            for size_name in customized_theme.font_sizes:
                customized_theme.font_sizes[size_name] = int(
                    customized_theme.font_sizes[size_name] * preferences.font_size_multiplier
                )

        # Apply custom colors
        for color_name, color_value in preferences.custom_colors.items():
            if color_name in customized_theme.colors:
                customized_theme.colors[color_name] = Color.from_hex(color_value, color_name)

        # Apply high contrast if enabled
        if preferences.high_contrast_enabled and theme.theme_type != ThemeType.HIGH_CONTRAST:
            customized_theme = await self._apply_high_contrast(customized_theme)

        # Apply blue light filter if enabled
        if preferences.blue_light_filter_enabled and theme.theme_type != ThemeType.BLUE_LIGHT:
            customized_theme = await self._apply_blue_light_filter(customized_theme)

        return customized_theme

    async def _apply_high_contrast(self, theme: Theme) -> Theme:
        """Apply high contrast adjustments to theme"""
        # Increase contrast ratios
        theme.colors['background'] = Color.from_hex('#000000', 'background')
        theme.colors['text_primary'] = Color.from_hex('#ffffff', 'text_primary')
        theme.colors['border'] = Color.from_hex('#ffffff', 'border')

        # Increase font sizes
        for size_name in theme.font_sizes:
            theme.font_sizes[size_name] = int(theme.font_sizes[size_name] * 1.2)

        # Increase border widths
        theme.borders['width_medium'] = 3
        theme.borders['width_thick'] = 5

        return theme

    async def _apply_blue_light_filter(self, theme: Theme) -> Theme:
        """Apply blue light filter to theme"""
        # Reduce blue light in colors
        for color_name, color in theme.colors.items():
            adjusted_color = self.color_generator.reduce_blue_light(color)
            theme.colors[color_name] = adjusted_color

        return theme

    def _compile_theme(self, theme: Theme) -> Dict[str, Any]:
        """Compile theme for efficient application"""
        compiled = {
            'css_variables': {},
            'font_families': {},
            'font_sizes': {},
            'spacing': {},
            'colors': {},
            'shadows': {},
            'animations': {},
            'borders': {}
        }

        # CSS variables for colors
        for name, color in theme.colors.items():
            compiled['css_variables'][f'--color-{name}'] = color.hex_value
            compiled['colors'][name] = {
                'hex': color.hex_value,
                'rgb': color.rgb,
                'hsl': color.hsl
            }

        # Font families
        for name, font in theme.fonts.items():
            compiled['font_families'][name] = font.value

        # Font sizes
        compiled['font_sizes'] = theme.font_sizes

        # Spacing
        compiled['spacing'] = theme.spacing

        # Shadows
        compiled['shadows'] = theme.shadows

        # Animations
        compiled['animations'] = theme.animations

        # Borders
        compiled['borders'] = theme.borders

        return compiled

    async def _apply_theme_immediately(self, user_id: str, compiled_theme: Dict[str, Any]):
        """Apply theme immediately without transition"""
        # This would integrate with the actual UI framework
        # For now, we'll simulate the application
        self.logger.info(f"Applying theme immediately for user {user_id}")

    async def _transition_theme(self, user_id: str, new_theme_id: str):
        """Transition between themes with animation"""
        if self.theme_transition_active:
            await self._apply_theme_immediately(user_id, self.compiled_themes[user_id])
            return

        self.theme_transition_active = True

        try:
            # Start transition animation
            await self._start_theme_transition_animation()

            # Apply new theme
            new_theme = self.themes[new_theme_id]
            preferences = self.theme_preferences.get(user_id)
            customized_theme = await self._apply_user_customizations(new_theme, preferences)
            compiled_theme = self._compile_theme(customized_theme)

            # Apply new theme
            await self._apply_theme_immediately(user_id, compiled_theme)

            # Complete transition
            await self._complete_theme_transition_animation()

        except Exception as e:
            self.logger.error(f"Error during theme transition: {e}")
        finally:
            self.theme_transition_active = False

    async def _start_theme_transition_animation(self):
        """Start theme transition animation"""
        # This would implement smooth transition animation
        await asyncio.sleep(0.1)  # Simulate transition start

    async def _complete_theme_transition_animation(self):
        """Complete theme transition animation"""
        # This would complete the transition animation
        await asyncio.sleep(0.2)  # Simulate transition completion

    async def create_custom_theme(self, user_id: str, theme_data: Dict[str, Any]) -> str:
        """Create custom theme"""
        theme_id = f"custom_{user_id}_{int(datetime.now().timestamp())}"

        # Parse colors
        colors = {}
        for color_name, color_value in theme_data.get('colors', {}).items():
            colors[color_name] = Color.from_hex(color_value, color_name)

        # Parse fonts
        fonts = {}
        for font_name, font_value in theme_data.get('fonts', {}).items():
            fonts[font_name] = FontFamily(font_value)

        # Get base theme for defaults
        base_theme_id = theme_data.get('base_theme', 'light_default')
        base_theme = self.themes.get(base_theme_id, self._create_light_theme())

        # Create custom theme
        custom_theme = Theme(
            theme_id=theme_id,
            name=theme_data.get('name', 'Custom Theme'),
            theme_type=ThemeType.CUSTOM,
            color_scheme=ColorScheme(theme_data.get('color_scheme', 'default')),
            colors={**base_theme.colors, **colors},
            fonts={**base_theme.fonts, **fonts},
            font_sizes=theme_data.get('font_sizes', base_theme.font_sizes),
            spacing=theme_data.get('spacing', base_theme.spacing),
            borders=theme_data.get('borders', base_theme.borders),
            shadows=theme_data.get('shadows', base_theme.shadows),
            animations=theme_data.get('animations', base_theme.animations),
            custom_css=theme_data.get('custom_css', ''),
            metadata={
                'created_at': datetime.now().isoformat(),
                'author': user_id,
                'version': '1.0',
                'base_theme': base_theme_id
            }
        )

        self.themes[theme_id] = custom_theme

        # Add to user's saved themes
        if user_id in self.theme_preferences:
            if theme_id not in self.theme_preferences[user_id].saved_themes:
                self.theme_preferences[user_id].saved_themes.append(theme_id)

        self.logger.info(f"Created custom theme {theme_id} for user {user_id}")
        return theme_id

    async def generate_theme_from_image(self, user_id: str, image_data: bytes, theme_name: str) -> str:
        """Generate theme from image colors"""
        # Extract dominant colors from image
        dominant_colors = await self.color_generator.extract_colors_from_image(image_data)

        # Generate color palette
        color_palette = self.color_palette_generator.generate_palette_from_colors(dominant_colors)

        # Create theme data
        theme_data = {
            'name': theme_name,
            'colors': {
                'primary': color_palette['primary'].hex_value,
                'secondary': color_palette['secondary'].hex_value,
                'accent': color_palette['accent'].hex_value,
                'background': color_palette['background'].hex_value,
                'text_primary': color_palette['text_primary'].hex_value
            },
            'base_theme': 'light_default'
        }

        return await self.create_custom_theme(user_id, theme_data)

    async def get_theme_variations(self, theme_id: str) -> Dict[str, str]:
        """Get variations of a theme"""
        if theme_id not in self.themes:
            return {}

        base_theme = self.themes[theme_id]
        variations = {}

        # Generate light/dark variations
        if base_theme.theme_type == ThemeType.LIGHT:
            dark_colors = {}
            for color_name, color in base_theme.colors.items():
                dark_colors[color_name] = self.color_generator.invert_for_dark_mode(color)

            dark_theme_id = f"{theme_id}_dark"
            dark_theme = Theme(
                theme_id=dark_theme_id,
                name=f"{base_theme.name} (Dark)",
                theme_type=ThemeType.DARK,
                color_scheme=base_theme.color_scheme,
                colors=dark_colors,
                fonts=base_theme.fonts,
                font_sizes=base_theme.font_sizes,
                spacing=base_theme.spacing,
                borders=base_theme.borders,
                shadows=base_theme.shadows,
                animations=base_theme.animations,
                custom_css=base_theme.custom_css,
                metadata={**base_theme.metadata, 'variation_of': theme_id}
            )
            self.themes[dark_theme_id] = dark_theme
            variations['dark'] = dark_theme_id

        elif base_theme.theme_type == ThemeType.DARK:
            light_colors = {}
            for color_name, color in base_theme.colors.items():
                light_colors[color_name] = self.color_generator.invert_for_light_mode(color)

            light_theme_id = f"{theme_id}_light"
            light_theme = Theme(
                theme_id=light_theme_id,
                name=f"{base_theme.name} (Light)",
                theme_type=ThemeType.LIGHT,
                color_scheme=base_theme.color_scheme,
                colors=light_colors,
                fonts=base_theme.fonts,
                font_sizes=base_theme.font_sizes,
                spacing=base_theme.spacing,
                borders=base_theme.borders,
                shadows=base_theme.shadows,
                animations=base_theme.animations,
                custom_css=base_theme.custom_css,
                metadata={**base_theme.metadata, 'variation_of': theme_id}
            )
            self.themes[light_theme_id] = light_theme
            variations['light'] = light_theme_id

        return variations

    def get_available_themes(self, user_id: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """Get available themes for user"""
        available_themes = {}

        for theme_id, theme in self.themes.items():
            theme_info = {
                'id': theme.theme_id,
                'name': theme.name,
                'type': theme.theme_type.value,
                'color_scheme': theme.color_scheme.value,
                'preview_colors': {
                    'primary': theme.colors.get('primary', Color.from_hex('#000000')).hex_value,
                    'background': theme.colors.get('background', Color.from_hex('#ffffff')).hex_value,
                    'text_primary': theme.colors.get('text_primary', Color.from_hex('#000000')).hex_value
                },
                'metadata': theme.metadata
            }
            available_themes[theme_id] = theme_info

        # Add user's custom themes
        if user_id and user_id in self.theme_preferences:
            for custom_theme_id in self.theme_preferences[user_id].saved_themes:
                if custom_theme_id in self.themes:
                    available_themes[custom_theme_id]['is_custom'] = True

        return available_themes

    def get_current_theme(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user's current theme"""
        theme_id = self.current_themes.get(user_id)
        if not theme_id or theme_id not in self.themes:
            return None

        theme = self.themes[theme_id]
        compiled_theme = self.compiled_themes.get(user_id, {})

        return {
            'id': theme.theme_id,
            'name': theme.name,
            'type': theme.theme_type.value,
            'color_scheme': theme.color_scheme.value,
            'compiled': compiled_theme,
            'metadata': theme.metadata
        }

    async def update_theme_preferences(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """Update user theme preferences"""
        if user_id not in self.theme_preferences:
            return False

        preferences = self.theme_preferences[user_id]

        # Apply updates
        for key, value in updates.items():
            if hasattr(preferences, key):
                if key == 'preferred_theme_type':
                    preferences.preferred_theme_type = ThemeType(value)
                elif key == 'preferred_color_scheme':
                    preferences.preferred_color_scheme = ColorScheme(value)
                elif key in ['light_theme_start', 'dark_theme_start']:
                    setattr(preferences, key, time.fromisoformat(value))
                else:
                    setattr(preferences, key, value)

        # Reapply theme if needed
        if 'preferred_theme_type' in updates or 'preferred_color_scheme' in updates:
            new_theme_id = self._find_theme_id_for_type(
                preferences.preferred_theme_type,
                preferences.preferred_color_scheme
            )
            await self.apply_theme(user_id, new_theme_id)

        self.logger.info(f"Updated theme preferences for user {user_id}")
        return True

    def get_theme_analytics(self, user_id: Optional[str] = None, time_range: int = 30) -> Dict[str, Any]:
        """Get theme usage analytics"""
        cutoff_date = datetime.now() - timedelta(days=time_range)

        analytics = {
            'time_range_days': time_range,
            'user_id': user_id,
            'total_themes': len(self.themes),
            'theme_types': {
                theme_type.value: sum(1 for t in self.themes.values() if t.theme_type == theme_type)
                for theme_type in ThemeType
            },
            'color_schemes': {
                scheme.value: sum(1 for t in self.themes.values() if t.color_scheme == scheme)
                for scheme in ColorScheme
            },
            'custom_themes': sum(1 for t in self.themes.values() if t.theme_type == ThemeType.CUSTOM),
            'current_usage': self._get_current_theme_usage(),
            'popular_themes': self._get_popular_themes()
        }

        return analytics

    def _get_current_theme_usage(self) -> Dict[str, int]:
        """Get current theme usage statistics"""
        usage = {}
        for theme_id in self.current_themes.values():
            usage[theme_id] = usage.get(theme_id, 0) + 1
        return usage

    def _get_popular_themes(self) -> List[Dict[str, Any]]:
        """Get most popular themes"""
        usage = self._get_current_theme_usage()
        popular = []

        for theme_id, count in usage.items():
            if theme_id in self.themes:
                theme = self.themes[theme_id]
                popular.append({
                    'theme_id': theme_id,
                    'name': theme.name,
                    'usage_count': count,
                    'type': theme.theme_type.value,
                    'color_scheme': theme.color_scheme.value
                })

        return sorted(popular, key=lambda x: x['usage_count'], reverse=True)

    async def export_theme(self, theme_id: str) -> Optional[Dict[str, Any]]:
        """Export theme configuration"""
        if theme_id not in self.themes:
            return None

        theme = self.themes[theme_id]

        export_data = {
            'theme_id': theme.theme_id,
            'name': theme.name,
            'type': theme.theme_type.value,
            'color_scheme': theme.color_scheme.value,
            'colors': {name: color.hex_value for name, color in theme.colors.items()},
            'fonts': {name: font.value for name, font in theme.fonts.items()},
            'font_sizes': theme.font_sizes,
            'spacing': theme.spacing,
            'borders': theme.borders,
            'shadows': theme.shadows,
            'animations': theme.animations,
            'custom_css': theme.custom_css,
            'metadata': theme.metadata,
            'export_timestamp': datetime.now().isoformat()
        }

        return export_data

    async def import_theme(self, user_id: str, theme_data: Dict[str, Any]) -> str:
        """Import theme configuration"""
        # Generate unique ID
        theme_id = f"imported_{user_id}_{int(datetime.now().timestamp())}"

        # Validate and create theme
        colors = {}
        for color_name, color_value in theme_data.get('colors', {}).items():
            colors[color_name] = Color.from_hex(color_value, color_name)

        fonts = {}
        for font_name, font_value in theme_data.get('fonts', {}).items():
            try:
                fonts[font_name] = FontFamily(font_value)
            except ValueError:
                fonts[font_name] = FontFamily.SANS_SERIF  # Default fallback

        imported_theme = Theme(
            theme_id=theme_id,
            name=theme_data.get('name', 'Imported Theme'),
            theme_type=ThemeType(theme_data.get('type', 'custom')),
            color_scheme=ColorScheme(theme_data.get('color_scheme', 'default')),
            colors=colors,
            fonts=fonts,
            font_sizes=theme_data.get('font_sizes', {}),
            spacing=theme_data.get('spacing', {}),
            borders=theme_data.get('borders', {}),
            shadows=theme_data.get('shadows', {}),
            animations=theme_data.get('animations', {}),
            custom_css=theme_data.get('custom_css', ''),
            metadata={
                **theme_data.get('metadata', {}),
                'imported_at': datetime.now().isoformat(),
                'imported_by': user_id
            }
        )

        self.themes[theme_id] = imported_theme

        # Add to user's saved themes
        if user_id in self.theme_preferences:
            if theme_id not in self.theme_preferences[user_id].saved_themes:
                self.theme_preferences[user_id].saved_themes.append(theme_id)

        self.logger.info(f"Imported theme {theme_id} for user {user_id}")
        return theme_id

    async def cleanup(self):
        """Cleanup theme manager"""
        if self.auto_switch_task:
            self.auto_switch_task.cancel()
            try:
                await self.auto_switch_task
            except asyncio.CancelledError:
                pass


class ColorGenerator:
    """Color generation and manipulation utilities"""

    def reduce_blue_light(self, color: Color) -> Color:
        """Reduce blue light in color for eye comfort"""
        r, g, b = color.rgb
        # Reduce blue channel
        new_b = int(b * 0.7)
        # Slightly increase red and orange tones
        new_r = min(255, int(r * 1.1))
        new_g = min(255, int(g * 1.05))

        new_hex = '#{:02x}{:02x}{:02x}'.format(new_r, new_g, new_b)
        return Color.from_hex(new_hex, f"{color.name}_blue_light_reduced")

    def invert_for_dark_mode(self, color: Color) -> Color:
        """Invert color for dark mode"""
        r, g, b = color.rgb
        # Invert with adjustments for better readability
        new_r = 255 - r
        new_g = 255 - g
        new_b = 255 - b

        # Adjust brightness
        h, s, l = Color._rgb_to_hsl((new_r, new_g, new_b))
        l = max(20, min(80, l))  # Keep within readable range
        new_rgb = Color._hsl_to_rgb((h / 360, s / 100, l / 100))

        new_hex = '#{:02x}{:02x}{:02x}'.format(*new_rgb)
        return Color.from_hex(new_hex, f"{color.name}_dark_mode")

    def invert_for_light_mode(self, color: Color) -> Color:
        """Invert color for light mode"""
        r, g, b = color.rgb
        # Invert with adjustments
        new_r = 255 - r
        new_g = 255 - g
        new_b = 255 - b

        # Adjust for light mode
        h, s, l = Color._rgb_to_hsl((new_r, new_g, new_b))
        l = max(15, min(85, l))  # Keep within readable range
        new_rgb = Color._hsl_to_rgb((h / 360, s / 100, l / 100))

        new_hex = '#{:02x}{:02x}{:02x}'.format(*new_rgb)
        return Color.from_hex(new_hex, f"{color.name}_light_mode")

    async def extract_colors_from_image(self, image_data: bytes) -> List[Color]:
        """Extract dominant colors from image"""
        # This would integrate with image processing library
        # For now, return placeholder colors
        return [
            Color.from_hex('#007bff', 'extracted_1'),
            Color.from_hex('#6c757d', 'extracted_2'),
            Color.from_hex('#28a745', 'extracted_3'),
            Color.from_hex('#dc3545', 'extracted_4'),
            Color.from_hex('#ffc107', 'extracted_5')
        ]


class ColorPaletteGenerator:
    """Generate color palettes from base colors"""

    def get_primary_color(self, color_scheme: ColorScheme) -> Color:
        """Get primary color for color scheme"""
        primary_colors = {
            ColorScheme.DEFAULT: Color.from_hex('#007bff', 'primary'),
            ColorScheme.BLUE: Color.from_hex('#0056b3', 'primary'),
            ColorScheme.GREEN: Color.from_hex('#28a745', 'primary'),
            ColorScheme.PURPLE: Color.from_hex('#6f42c1', 'primary'),
            ColorScheme.RED: Color.from_hex('#dc3545', 'primary'),
            ColorScheme.ORANGE: Color.from_hex('#fd7e14', 'primary'),
            ColorScheme.TEAL: Color.from_hex('#20c997', 'primary'),
            ColorScheme.INDIGO: Color.from_hex('#6610f2', 'primary'),
            ColorScheme.PINK: Color.from_hex('#e83e8c', 'primary'),
            ColorScheme.GRAY: Color.from_hex('#6c757d', 'primary')
        }
        return primary_colors.get(color_scheme, primary_colors[ColorScheme.DEFAULT])

    def generate_palette(self, primary_color: Color) -> Dict[str, Color]:
        """Generate complete color palette from primary color"""
        h, s, l = primary_color.hsl

        # Generate complementary colors
        secondary_hue = (h + 30) % 360  # Analogous
        accent_hue = (h + 180) % 360  # Complementary

        palette = {
            'primary': primary_color,
            'secondary': Color.from_hsl(secondary_hue, s * 0.8, l),
            'accent': Color.from_hsl(accent_hue, s * 0.9, l),
            'background': Color.from_hsl(h, s * 0.1, 95 if l > 50 else 10),
            'surface': Color.from_hsl(h, s * 0.15, 98 if l > 50 else 15),
            'text_primary': Color.from_hsl(h, s * 0.1, 15 if l > 50 else 90),
            'text_secondary': Color.from_hsl(h, s * 0.2, 35 if l > 50 else 70),
            'border': Color.from_hsl(h, s * 0.2, 85 if l > 50 else 25),
            'shadow': Color.from_hsl(0, 0, 20 if l > 50 else 80)
        }

        return palette

    def generate_palette_from_colors(self, colors: List[Color]) -> Dict[str, Color]:
        """Generate palette from extracted colors"""
        if not colors:
            return self.generate_palette(Color.from_hex('#007bff', 'default_primary'))

        # Use most prominent color as primary
        primary_color = colors[0]

        # Generate palette from primary
        palette = self.generate_palette(primary_color)

        # Try to use other extracted colors for secondary/accent if they fit
        if len(colors) > 1:
            palette['secondary'] = colors[1]
        if len(colors) > 2:
            palette['accent'] = colors[2]

        return palette


# Extend Color class with from_hsl method
Color.from_hsl = classmethod(lambda cls, h, s, l: cls.from_hex(cls._hsl_to_rgb((h, s, l)), f"hsl_{h}_{s}_{l}"))


# Helper functions for integration
async def create_theme_manager(config: Dict[str, Any] = None) -> ThemeManager:
    """Create and initialize theme manager"""
    return ThemeManager(config)

# Example usage
if __name__ == "__main__":
    async def main():
        # Initialize theme manager
        theme_manager = await create_theme_manager()

        # Create theme preferences
        preference_data = {
            'preferred_theme_type': 'light',
            'preferred_color_scheme': 'blue',
            'auto_switch_enabled': True,
            'font_size_multiplier': 1.0
        }

        preferences = await theme_manager.create_theme_preferences("user123", preference_data)
        print("Created theme preferences:", preferences)

        # Apply theme
        success = await theme_manager.apply_theme("user123", "light_blue")
        print("Applied theme:", success)

        # Get available themes
        available_themes = theme_manager.get_available_themes("user123")
        print(f"Available themes: {len(available_themes)}")

        # Create custom theme
        custom_theme_data = {
            'name': 'My Custom Theme',
            'colors': {
                'primary': '#ff6b6b',
                'secondary': '#4ecdc4',
                'background': '#f8f9fa'
            },
            'base_theme': 'light_default'
        }

        custom_theme_id = await theme_manager.create_custom_theme("user123", custom_theme_data)
        print("Created custom theme:", custom_theme_id)

        # Get current theme
        current_theme = theme_manager.get_current_theme("user123")
        print("Current theme:", current_theme)

        # Get analytics
        analytics = theme_manager.get_theme_analytics("user123")
        print("Theme analytics:", analytics)

        # Cleanup
        await theme_manager.cleanup()

    asyncio.run(main())