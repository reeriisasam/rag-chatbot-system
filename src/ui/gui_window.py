import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
from typing import Callable, Optional
from datetime import datetime
from loguru import logger

class ChatGUI:
    """GUI Window สำหรับ Chatbot แบบ OpenCV style"""
    
    def __init__(self, title: str = "RAG Chatbot System", config: dict = None):
        self.config = config or {}
        self.root = tk.Tk()
        self.root.title(title)
        
        # ตั้งค่าขนาดหน้าต่าง
        self.window_width = 900
        self.window_height = 700
        
        # จัดหน้าต่างให้อยู่กลางจอ
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - self.window_width) // 2
        y = (screen_height - self.window_height) // 2
        self.root.geometry(f"{self.window_width}x{self.window_height}+{x}+{y}")
        
        # ตั้งค่าสี
        self.bg_color = "#1e1e1e"
        self.chat_bg = "#2d2d2d"
        self.user_color = "#00ff88"
        self.bot_color = "#00bfff"
        self.system_color = "#ffaa00"
        
        # Callbacks
        self.on_send_callback = None
        self.on_voice_callback = None
        self.on_close_callback = None
        
        # Mode
        self.current_mode = "text"
        self.is_processing = False
        
        self._setup_ui()
        self._setup_styles()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
    def _setup_styles(self):
        """ตั้งค่า ttk styles"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Button style
        style.configure(
            "Custom.TButton",
            background="#0078d4",
            foreground="white",
            borderwidth=0,
            focuscolor="none",
            font=("Segoe UI", 10)
        )
        style.map("Custom.TButton",
            background=[('active', '#106ebe'), ('pressed', '#005a9e')]
        )
        
        # Voice button style
        style.configure(
            "Voice.TButton",
            background="#dc3545",
            foreground="white",
            borderwidth=0,
            focuscolor="none",
            font=("Segoe UI", 10)
        )
        style.map("Voice.TButton",
            background=[('active', '#c82333'), ('pressed', '#bd2130')]
        )
        
    def _setup_ui(self):
        """สร้าง UI components"""
        self.root.configure(bg=self.bg_color)
        
        # Main container
        main_frame = tk.Frame(self.root, bg=self.bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # ===== Header =====
        header_frame = tk.Frame(main_frame, bg=self.bg_color)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Title
        title_label = tk.Label(
            header_frame,
            text="🤖 RAG Chatbot System",
            font=("Segoe UI", 18, "bold"),
            bg=self.bg_color,
            fg="white"
        )
        title_label.pack(side=tk.LEFT)
        
        # Status label
        self.status_label = tk.Label(
            header_frame,
            text="● Online",
            font=("Segoe UI", 10),
            bg=self.bg_color,
            fg="#00ff88"
        )
        self.status_label.pack(side=tk.RIGHT, padx=10)
        
        # Mode label
        self.mode_label = tk.Label(
            header_frame,
            text="Mode: Text",
            font=("Segoe UI", 10),
            bg=self.bg_color,
            fg="#00bfff"
        )
        self.mode_label.pack(side=tk.RIGHT)
        
        # ===== Chat Area =====
        chat_frame = tk.Frame(main_frame, bg=self.chat_bg)
        chat_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Chat display (ScrolledText)
        self.chat_display = scrolledtext.ScrolledText(
            chat_frame,
            wrap=tk.WORD,
            font=("Consolas", 10),
            bg=self.chat_bg,
            fg="white",
            insertbackground="white",
            relief=tk.FLAT,
            padx=10,
            pady=10,
            state=tk.DISABLED
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True)
        
        # Configure tags for colors
        self.chat_display.tag_config("user", foreground=self.user_color, font=("Consolas", 10, "bold"))
        self.chat_display.tag_config("bot", foreground=self.bot_color, font=("Consolas", 10, "bold"))
        self.chat_display.tag_config("system", foreground=self.system_color, font=("Consolas", 10, "italic"))
        self.chat_display.tag_config("time", foreground="#888888", font=("Consolas", 8))
        self.chat_display.tag_config("metadata", foreground="#888888", font=("Consolas", 9, "italic"))
        
        # ===== Input Area =====
        input_frame = tk.Frame(main_frame, bg=self.bg_color)
        input_frame.pack(fill=tk.X)
        
        # Input text box
        self.input_text = tk.Text(
            input_frame,
            height=3,
            font=("Segoe UI", 11),
            bg="#3d3d3d",
            fg="white",
            insertbackground="white",
            relief=tk.FLAT,
            padx=10,
            pady=10
        )
        self.input_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Bind Enter key
        self.input_text.bind("<Return>", self._on_enter_key)
        self.input_text.bind("<Shift-Return>", lambda e: None)  # Allow Shift+Enter for new line
        
        # Buttons frame
        buttons_frame = tk.Frame(input_frame, bg=self.bg_color)
        buttons_frame.pack(side=tk.RIGHT)
        
        # Send button
        self.send_button = ttk.Button(
            buttons_frame,
            text="Send ➤",
            style="Custom.TButton",
            command=self._on_send_click,
            width=12
        )
        self.send_button.pack(pady=(0, 5))
        
        # Voice button
        self.voice_button = ttk.Button(
            buttons_frame,
            text="🎤 Voice",
            style="Voice.TButton",
            command=self._on_voice_click,
            width=12
        )
        self.voice_button.pack(pady=(5, 0))
        
        # ===== Bottom toolbar =====
        toolbar_frame = tk.Frame(main_frame, bg=self.bg_color)
        toolbar_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Clear button
        clear_btn = tk.Button(
            toolbar_frame,
            text="🗑️ Clear",
            font=("Segoe UI", 9),
            bg="#3d3d3d",
            fg="white",
            relief=tk.FLAT,
            padx=15,
            pady=5,
            command=self.clear_chat
        )
        clear_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Mode toggle button
        self.mode_toggle_btn = tk.Button(
            toolbar_frame,
            text="📝 Text Mode",
            font=("Segoe UI", 9),
            bg="#3d3d3d",
            fg="white",
            relief=tk.FLAT,
            padx=15,
            pady=5,
            command=self.toggle_mode
        )
        self.mode_toggle_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Voice indicator label with animation
        self.voice_indicator = tk.Label(
            toolbar_frame,
            text="",
            font=("Segoe UI", 9),
            bg=self.bg_color,
            fg="#00ff88"
        )
        self.voice_indicator.pack(side=tk.LEFT, padx=(10, 5))
        
        # Voice visualization canvas
        self.voice_canvas = tk.Canvas(
            toolbar_frame,
            width=100,
            height=20,
            bg=self.bg_color,
            highlightthickness=0
        )
        self.voice_canvas.pack(side=tk.LEFT, padx=(5, 5))
        
        # Animation state
        self.is_animating = False
        self.animation_bars = []
        
        # Stop speaking button
        self.stop_speaking_btn = tk.Button(
            toolbar_frame,
            text="🔇 Stop",
            font=("Segoe UI", 9),
            bg="#3d3d3d",
            fg="white",
            relief=tk.FLAT,
            padx=15,
            pady=5,
            command=self.stop_speaking,
            state=tk.DISABLED
        )
        self.stop_speaking_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Initialize callback
        self.stop_speaking_callback = None
        self.voice_mode_active = False
        
        # Stats button
        stats_btn = tk.Button(
            toolbar_frame,
            text="📊 Stats",
            font=("Segoe UI", 9),
            bg="#3d3d3d",
            fg="white",
            relief=tk.FLAT,
            padx=15,
            pady=5,
            command=self.show_stats
        )
        stats_btn.pack(side=tk.LEFT)
        
        # Show welcome message
        self._show_welcome()
        
    def _show_welcome(self):
        """แสดงข้อความต้อนรับ"""
        welcome = """╔══════════════════════════════════════════════════════════════╗
║           🤖 RAG Chatbot System - v1.0                       ║
╚══════════════════════════════════════════════════════════════╝

ยินดีต้อนรับสู่ระบบ RAG Chatbot!

คำสั่งที่ใช้ได้:
  /help    - แสดงคำสั่งทั้งหมด
  /clear   - ล้างหน้าจอ
  /stats   - แสดงสถิติระบบ
  /reload  - โหลดเอกสารใหม่

เริ่มต้นใช้งาน:
  1. พิมพ์คำถามในช่องด้านล่าง
  2. กด Enter หรือคลิก Send
  3. หรือใช้ปุ่ม Voice สำหรับโหมดเสียง

════════════════════════════════════════════════════════════════
"""
        self.add_system_message(welcome)
        
    def add_message(self, role: str, content: str, metadata: dict = None):
        """
        เพิ่มข้อความในหน้าจอ
        
        Args:
            role: 'user', 'assistant', 'system'
            content: ข้อความ
            metadata: ข้อมูลเพิ่มเติม
        """
        self.chat_display.config(state=tk.NORMAL)
        
        # เพิ่มเวลา
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # เลือก tag และ prefix ตาม role
        if role == "user":
            tag = "user"
            prefix = "👤 You"
        elif role == "assistant":
            tag = "bot"
            prefix = "🤖 Assistant"
        else:
            tag = "system"
            prefix = "⚙️ System"
        
        # แสดงข้อความ
        self.chat_display.insert(tk.END, f"\n[{timestamp}] ", "time")
        self.chat_display.insert(tk.END, f"{prefix}:\n", tag)
        self.chat_display.insert(tk.END, f"{content}\n")
        
        # แสดง metadata ถ้ามี
        if metadata:
            if metadata.get('use_rag'):
                self.chat_display.insert(tk.END, "  📚 ใช้ข้อมูลจาก RAG\n", "metadata")
            if metadata.get('sources'):
                sources = ", ".join(metadata['sources'][:3])
                self.chat_display.insert(tk.END, f"  📄 แหล่งที่มา: {sources}\n", "metadata")
        
        self.chat_display.insert(tk.END, "─" * 70 + "\n")
        
        # Scroll to bottom
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
        
    def add_user_message(self, content: str):
        """เพิ่มข้อความของ user"""
        self.add_message("user", content)
        
    def add_bot_message(self, content: str, metadata: dict = None):
        """เพิ่มข้อความของ bot"""
        self.add_message("assistant", content, metadata)
        
    def add_system_message(self, content: str):
        """เพิ่มข้อความของ system"""
        self.add_message("system", content)
        
    def clear_chat(self):
        """ล้างหน้าจอ"""
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete(1.0, tk.END)
        self.chat_display.config(state=tk.DISABLED)
        self._show_welcome()
        
    def get_input(self) -> str:
        """ดึงข้อความจาก input box"""
        return self.input_text.get(1.0, tk.END).strip()
        
    def clear_input(self):
        """ล้าง input box"""
        self.input_text.delete(1.0, tk.END)
        
    def set_processing(self, is_processing: bool):
        """ตั้งค่าสถานะการประมวลผล"""
        self.is_processing = is_processing
        
        if is_processing:
            self.send_button.config(state=tk.DISABLED)
            self.voice_button.config(state=tk.DISABLED)
            self.input_text.config(state=tk.DISABLED)
            self.status_label.config(text="● Processing...", fg="#ffaa00")
        else:
            self.send_button.config(state=tk.NORMAL)
            self.voice_button.config(state=tk.NORMAL)
            self.input_text.config(state=tk.NORMAL)
            self.status_label.config(text="● Online", fg="#00ff88")
            
    def toggle_mode(self):
        """สลับโหมด text/voice"""
        if self.current_mode == "text":
            self.current_mode = "voice"
            self.voice_mode_active = True
            self.mode_label.config(text="Mode: Voice 🎤")
            self.mode_toggle_btn.config(text="🎤 Voice Mode (Active)")
            self.add_system_message("🎤 เปิดโหมดเสียงแล้ว - กดปุ่ม Voice เพื่อเริ่มสนทนา")
            # เปลี่ยนสีปุ่ม Voice
            self.voice_button.config(style="Voice.TButton")
        else:
            self.current_mode = "text"
            self.voice_mode_active = False
            self.mode_label.config(text="Mode: Text 📝")
            self.mode_toggle_btn.config(text="📝 Text Mode")
            self.add_system_message("📝 เปลี่ยนเป็นโหมดข้อความแล้ว")
            self.stop_voice_animation()
            # เปลี่ยนสีปุ่ม Voice กลับ
            self.voice_button.config(style="Custom.TButton")
            
    def show_stats(self):
        """แสดงสถิติ (placeholder)"""
        if hasattr(self, 'stats_callback') and self.stats_callback:
            self.stats_callback()
        else:
            self.add_system_message("สถิติระบบ: ฟังก์ชันนี้ยังไม่ได้เชื่อมต่อ")
            
    def show_error(self, message: str):
        """แสดง error"""
        messagebox.showerror("Error", message)
        
    def show_info(self, message: str):
        """แสดงข้อมูล"""
        messagebox.showinfo("Info", message)
        
    def _on_enter_key(self, event):
        """Handle Enter key"""
        if not event.state & 0x1:  # ไม่ได้กด Shift
            self._on_send_click()
            return "break"  # ป้องกันการขึ้นบรรทัดใหม่
        
    def _on_send_click(self):
        """Handle send button click"""
        if self.is_processing:
            return
            
        message = self.get_input()
        if not message:
            return
            
        # เรียก callback
        if self.on_send_callback:
            self.clear_input()
            threading.Thread(
                target=self.on_send_callback,
                args=(message,),
                daemon=True
            ).start()
            
    def _on_voice_click(self):
        """Handle voice button click"""
        if self.is_processing:
            return
            
        if self.on_voice_callback:
            threading.Thread(
                target=self.on_voice_callback,
                daemon=True
            ).start()
            
    def _on_closing(self):
        """Handle window close"""
        if messagebox.askokcancel("ออกจากโปรแกรม", "ต้องการออกจากโปรแกรมหรือไม่?"):
            if self.on_close_callback:
                self.on_close_callback()
            self.root.destroy()
            
    def set_send_callback(self, callback: Callable):
        """ตั้งค่า callback สำหรับการส่งข้อความ"""
        self.on_send_callback = callback
        
    def set_voice_callback(self, callback: Callable):
        """ตั้งค่า callback สำหรับปุ่มเสียง"""
        self.on_voice_callback = callback
        
    def set_close_callback(self, callback: Callable):
        """ตั้งค่า callback สำหรับการปิดหน้าต่าง"""
        self.on_close_callback = callback
        
    def set_stats_callback(self, callback: Callable):
        """ตั้งค่า callback สำหรับแสดงสถิติ"""
        self.stats_callback = callback
        
    def run(self):
        """เริ่มต้น GUI loop"""
        self.root.mainloop()
        
    def update_status(self, status: str, color: str = "#00ff88"):
        """อัพเดทสถานะ"""
        self.status_label.config(text=f"● {status}", fg=color)
    
    def show_voice_indicator(self, message: str):
        """แสดงสถานะเสียง"""
        self.voice_indicator.config(text=message, fg="#00bfff")
        self.stop_speaking_btn.config(state=tk.NORMAL)
        
        # เริ่ม animation
        if not self.is_animating:
            self.start_voice_animation()
    
    def hide_voice_indicator(self):
        """ซ่อนสถานะเสียง"""
        self.voice_indicator.config(text="")
        self.stop_speaking_btn.config(state=tk.DISABLED)
        self.stop_voice_animation()
    
    def start_voice_animation(self):
        """เริ่ม animation แสดงเสียง"""
        self.is_animating = True
        self._animate_voice()
    
    def stop_voice_animation(self):
        """หยุด animation"""
        self.is_animating = False
        self.voice_canvas.delete("all")
        self.animation_bars = []
    
    def _animate_voice(self):
        """Animation loop สำหรับแสดงเสียง"""
        if not self.is_animating:
            return
        
        # ล้าง canvas
        self.voice_canvas.delete("all")
        
        # สร้าง bars แสดงเสียง
        import random
        num_bars = 8
        bar_width = 8
        spacing = 4
        max_height = 20
        
        for i in range(num_bars):
            x = i * (bar_width + spacing) + 10
            height = random.randint(5, max_height)
            y1 = (max_height - height) // 2 + 2
            y2 = y1 + height
            
            # สีสลับกัน
            color = "#00bfff" if i % 2 == 0 else "#00ff88"
            
            self.voice_canvas.create_rectangle(
                x, y1, x + bar_width, y2,
                fill=color,
                outline=""
            )
        
        # เรียกตัวเองอีกครั้งหลัง 100ms
        if self.is_animating:
            self.root.after(100, self._animate_voice)
    
    def stop_speaking(self):
        """หยุดการพูด"""
        if hasattr(self, 'stop_speaking_callback') and self.stop_speaking_callback:
            self.stop_speaking_callback()
        self.hide_voice_indicator()
    
    def set_stop_speaking_callback(self, callback: Callable):
        """ตั้งค่า callback สำหรับหยุดการพูด"""
        self.stop_speaking_callback = callback