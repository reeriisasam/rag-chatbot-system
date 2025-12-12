#!/usr/bin/env python3
"""
ตรวจสอบการตั้งค่า API Configuration
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.config import get_config
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import requests

console = Console()

def check_config():
    """ตรวจสอบ configuration"""
    console.print("\n[bold cyan]🔍 ตรวจสอบการตั้งค่า RAG Chatbot[/bold cyan]\n")
    
    try:
        config = get_config()
        llm_config = config.config.get('llm', {})
        
        # สร้างตาราง
        table = Table(title="LLM Configuration", show_header=True)
        table.add_column("Setting", style="cyan", width=20)
        table.add_column("Value", style="white", width=50)
        table.add_column("Status", style="green", width=10)
        
        # Provider
        provider = llm_config.get('provider', 'N/A')
        table.add_row("Provider", provider, "✓" if provider else "✗")
        
        # Model
        model = llm_config.get('model_name', 'N/A')
        table.add_row("Model", model, "✓" if model else "✗")
        
        # API Key
        api_key = llm_config.get('api_key', 'N/A')
        if api_key and api_key != 'N/A':
            masked_key = f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else "***"
            table.add_row("API Key", masked_key, "✓")
        else:
            table.add_row("API Key", "ไม่พบ", "✗")
        
        # URL
        if provider == 'donmi':
            url = llm_config.get('api_url', llm_config.get('base_url', 'N/A'))
            url_label = "API URL"
        else:
            url = llm_config.get('base_url', 'N/A')
            url_label = "Base URL"
        
        table.add_row(url_label, url, "✓" if url and url != 'N/A' else "✗")
        
        # Temperature
        temp = llm_config.get('temperature', 'N/A')
        table.add_row("Temperature", str(temp), "✓")
        
        # Max Tokens
        max_tokens = llm_config.get('max_tokens', 'N/A')
        table.add_row("Max Tokens", str(max_tokens), "✓")
        
        # Donmi specific
        if provider == 'donmi':
            timeout = llm_config.get('timeout', 60)
            citation = llm_config.get('citation', False)
            response_mode = llm_config.get('response_mode', 'blocking')
            
            table.add_row("Timeout", f"{timeout}s", "✓")
            table.add_row("Citation", str(citation), "✓")
            table.add_row("Response Mode", response_mode, "✓")
        
        console.print(table)
        console.print()
        
        # ตรวจสอบปัญหา
        issues = []
        
        if not provider or provider == 'N/A':
            issues.append("❌ ไม่ได้ระบุ provider")
        
        if not api_key or api_key == 'N/A' or api_key == 'your-api-key-here':
            issues.append("❌ ไม่ได้ระบุ API Key หรือยังเป็นค่า example")
        
        if not url or url == 'N/A' or 'your-' in url:
            issues.append("❌ ไม่ได้ระบุ URL หรือยังเป็นค่า example")
        
        if issues:
            console.print(Panel(
                "\n".join(issues),
                title="[bold red]พบปัญหา[/bold red]",
                border_style="red"
            ))
            console.print("\n[yellow]💡 แนะนำ:[/yellow]")
            console.print("1. แก้ไขไฟล์ .env หรือ config.yaml")
            console.print("2. ใส่ค่า API Key และ URL ที่ถูกต้อง")
            console.print("3. ดูคู่มือใน API_SETUP.md หรือ DONMI_SETUP.md\n")
        else:
            console.print("[bold green]✅ การตั้งค่าถูกต้อง![/bold green]\n")
            
            # ทดสอบการเชื่อมต่อ
            if console.input("[yellow]ต้องการทดสอบการเชื่อมต่อ API หรือไม่? (y/n): [/yellow]").lower() == 'y':
                test_api_connection(llm_config, provider)
        
    except Exception as e:
        console.print(f"[bold red]❌ เกิดข้อผิดพลาด: {e}[/bold red]")


def test_api_connection(llm_config, provider):
    """ทดสอบการเชื่อมต่อ API"""
    console.print("\n[cyan]🔄 กำลังทดสอบการเชื่อมต่อ...[/cyan]\n")
    
    try:
        if provider == 'donmi':
            # ทดสอบ Donmi API
            api_url = llm_config.get('api_url') or llm_config.get('base_url')
            api_key = llm_config.get('api_key')
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            
            payload = {
                "inputs": {"question": "test"},
                "citation": False,
                "response_mode": "blocking"
            }
            
            console.print(f"URL: {api_url}")
            console.print("กำลังส่งคำขอ...\n")
            
            response = requests.post(
                api_url,
                headers=headers,
                json=payload,
                timeout=30,
                verify=False
            )
            
            console.print(f"Status Code: [bold]{response.status_code}[/bold]")
            
            if response.status_code == 200:
                result = response.json()
                console.print(f"\n[bold green]✅ เชื่อมต่อสำเร็จ![/bold green]")
                console.print(f"\nคำตอบ: {result.get('answer', 'N/A')[:100]}...")
            else:
                console.print(f"\n[bold red]❌ การเชื่อมต่อล้มเหลว[/bold red]")
                console.print(f"Response: {response.text[:200]}")
        
        else:
            # ทดสอบ OpenAI-compatible API
            from openai import OpenAI
            
            base_url = llm_config.get('base_url')
            api_key = llm_config.get('api_key')
            model = llm_config.get('model_name')
            
            console.print(f"URL: {base_url}")
            console.print(f"Model: {model}")
            console.print("กำลังส่งคำขอ...\n")
            
            client = OpenAI(
                base_url=base_url,
                api_key=api_key
            )
            
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=50
            )
            
            console.print(f"[bold green]✅ เชื่อมต่อสำเร็จ![/bold green]")
            console.print(f"\nคำตอบ: {response.choices[0].message.content}")
    
    except requests.exceptions.ConnectionError:
        console.print("[bold red]❌ ไม่สามารถเชื่อมต่อได้[/bold red]")
        console.print("\nตรวจสอบ:")
        console.print("  1. URL ถูกต้องหรือไม่")
        console.print("  2. เชื่อมต่ออินเทอร์เน็ตหรือไม่")
        console.print("  3. API service ทำงานอยู่หรือไม่")
    
    except requests.exceptions.Timeout:
        console.print("[bold red]❌ Timeout - API ไม่ตอบกลับ[/bold red]")
        console.print("\nลอง:")
        console.print("  1. เพิ่ม timeout ใน config")
        console.print("  2. ตรวจสอบว่า API ทำงานช้าหรือไม่")
    
    except Exception as e:
        console.print(f"[bold red]❌ เกิดข้อผิดพลาด: {e}[/bold red]")
        console.print(f"\nDetails: {str(e)}")


if __name__ == "__main__":
    check_config()