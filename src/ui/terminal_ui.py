from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich.live import Live
from rich.table import Table
from rich.text import Text
from typing import Dict, Any, Optional
from loguru import logger
import sys

class TerminalUI:
    """Terminal UI สำหรับ Chatbot"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.console = Console()
        self.mode = config.get('mode', 'auto')
        
        # สี
        self.bot_color = config.get('colors', {}).get('bot', 'cyan')
        self.user_color = config.get('colors', {}).get('user', 'green')
        self.system_color = config.get('colors', {}).get('system', 'yellow')
        
        # สัญลักษณ์
        self.bot_symbol = "🤖"
        self.user_symbol = "👤"
        self.system_symbol = "⚙️"
    
    def show_welcome(self):
        """แสดงข้อความต้อนรับ"""
        welcome_text = """
# 🤖 RAG Chatbot System

ยินดีต้อนรับสู่ระบบแชทบอท RAG!

**โหมดการใช้งาน:**
- `text` - พิมพ์ข้อความเพื่อสนทนา
- `voice` - ใช้เสียงพูดเพื่อสนทนา (ต้องติดตั้ง audio packages)
- `exit` / `quit` - ออกจากโปรแกรม

**คำสั่งพิเศษ:**
- `/mode text` - เปลี่ยนเป็นโหมดข้อความ
- `/mode voice` - เปลี่ยนเป็นโหมดเสียง
- `/clear` - ล้างหน้าจอ
- `/help` - แสดงความช่วยเหลือ
- `/stats` - แสดงสถิติระบบ
"""
        self.console.print(Panel(
            Markdown(welcome_text),
            title="[bold cyan]ยินดีต้อนรับ[/bold cyan]",
            border_style="cyan"
        ))
        self.console.print()
    
    def show_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """
        แสดงข้อความในรูปแบบสวยงาม
        
        Args:
            role: บทบาท ('user', 'assistant', 'system')
            content: เนื้อหาข้อความ
            metadata: ข้อมูลเพิ่มเติม (optional)
        """
        if role == 'user':
            symbol = self.user_symbol
            color = self.user_color
            title = "คุณ"
        elif role == 'assistant':
            symbol = self.bot_symbol
            color = self.bot_color
            title = "Assistant"
        else:  # system
            symbol = self.system_symbol
            color = self.system_color
            title = "System"
        
        # สร้าง panel
        panel = Panel(
            content,
            title=f"[bold {color}]{symbol} {title}[/bold {color}]",
            border_style=color,
            padding=(0, 1)
        )
        
        self.console.print(panel)
        
        # แสดง metadata ถ้ามี
        if metadata:
            self._show_metadata(metadata)
        
        self.console.print()
    
    def _show_metadata(self, metadata: Dict):
        """แสดงข้อมูลเพิ่มเติม"""
        if metadata.get('use_rag'):
            self.console.print(
                f"  [dim]📚 ใช้ข้อมูลจาก RAG[/dim]",
                style="dim"
            )
        
        if metadata.get('sources'):
            sources = ", ".join(metadata['sources'][:3])
            self.console.print(
                f"  [dim]📄 แหล่งที่มา: {sources}[/dim]",
                style="dim"
            )
    
    def get_input(self, prompt: str = "คุณ") -> str:
        """
        รับ input จากผู้ใช้
        
        Args:
            prompt: ข้อความ prompt
        
        Returns:
            ข้อความที่ผู้ใช้พิมพ์
        """
        try:
            user_input = Prompt.ask(
                f"[bold {self.user_color}]{self.user_symbol} {prompt}[/bold {self.user_color}]"
            )
            return user_input.strip()
        except KeyboardInterrupt:
            return "exit"
        except EOFError:
            return "exit"
    
    def show_thinking(self, message: str = "กำลังคิด..."):
        """แสดงว่ากำลังประมวลผล"""
        self.console.print(
            f"[dim italic]{self.bot_symbol} {message}[/dim italic]"
        )
    
    def show_listening(self):
        """แสดงว่ากำลังฟังเสียง"""
        self.console.print(
            f"\n[bold yellow]🎤 กำลังฟัง... (พูดได้เลย)[/bold yellow]"
        )
    
    def show_error(self, error_message: str):
        """แสดงข้อความ error"""
        self.console.print(
            Panel(
                f"❌ {error_message}",
                title="[bold red]Error[/bold red]",
                border_style="red"
            )
        )
        self.console.print()
    
    def show_success(self, message: str):
        """แสดงข้อความสำเร็จ"""
        self.console.print(f"[bold green]✓ {message}[/bold green]")
        self.console.print()
    
    def show_info(self, message: str):
        """แสดงข้อมูล"""
        self.console.print(f"[bold {self.system_color}]ℹ️  {message}[/bold {self.system_color}]")
        self.console.print()
    
    def show_stats(self, stats: Dict[str, Any]):
        """
        แสดงสถิติระบบ
        
        Args:
            stats: ข้อมูลสถิติ
        """
        table = Table(title="📊 สถิติระบบ", show_header=False, border_style="cyan")
        table.add_column("ข้อมูล", style="cyan", width=30)
        table.add_column("ค่า", style="white")
        
        for key, value in stats.items():
            table.add_row(key, str(value))
        
        self.console.print(table)
        self.console.print()
    
    def show_help(self):
        """แสดงความช่วยเหลือ"""
        help_text = """
# 📖 คำสั่งที่ใช้ได้

## คำสั่งพื้นฐาน
- `exit` หรือ `quit` - ออกจากโปรแกรม
- `/help` - แสดงความช่วยเหลือนี้
- `/clear` - ล้างหน้าจอ

## การเปลี่ยนโหมด
- `/mode text` - เปลี่ยนเป็นโหมดข้อความ
- `/mode voice` - เปลี่ยนเป็นโหมดเสียง

## ข้อมูลระบบ
- `/stats` - แสดงสถิติระบบ
- `/info` - แสดงข้อมูล config

## การใช้งาน RAG
- พิมพ์คำถามที่ต้องการค้นหาจากเอกสาร
- ระบบจะค้นหาข้อมูลที่เกี่ยวข้องโดยอัตโนมัติ

## เคล็ดลับ
- ใช้คำว่า "จากเอกสาร" หรือ "ค้นหา" เพื่อบอกว่าต้องการใช้ RAG
- โหมดเสียงจะใช้ไมโครโฟนเพื่อรับเสียงและตอบกลับด้วยเสียง
"""
        self.console.print(Panel(
            Markdown(help_text),
            title="[bold cyan]ความช่วยเหลือ[/bold cyan]",
            border_style="cyan"
        ))
        self.console.print()
    
    def clear(self):
        """ล้างหน้าจอ"""
        self.console.clear()
    
    def show_goodbye(self):
        """แสดงข้อความลาก่อน"""
        goodbye = Text()
        goodbye.append("\n👋 ขอบคุณที่ใช้งาน RAG Chatbot!\n", style="bold cyan")
        goodbye.append("ยินดีให้บริการอีกครั้ง 😊\n", style="cyan")
        
        self.console.print(Panel(
            goodbye,
            border_style="cyan"
        ))
    
    def set_mode(self, mode: str):
        """เปลี่ยนโหมด"""
        self.mode = mode
        mode_text = "ข้อความ" if mode == "text" else "เสียง"
        self.show_success(f"เปลี่ยนเป็นโหมด{mode_text}แล้ว")
    
    def get_mode(self) -> str:
        """ดึงโหมดปัจจุบัน"""
        return self.mode