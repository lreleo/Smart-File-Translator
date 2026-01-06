import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, simpledialog, Menu
import requests
import json
import platform
import concurrent.futures  # 新增：用于多线程并发
import time  # 新增：用于延时
import random # 新增：用于随机延时
from deep_translator import GoogleTranslator

# 尝试开启 Windows 高分屏支持 (防止模糊)
try:
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)
except:
    pass

# 配置文件名
CONFIG_FILE = "translator_config.json"

# 常见音频扩展名
AUDIO_EXTENSIONS = {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma', '.aiff', '.alac', '.ape'}

# --- 现代配色方案 (2025 流行色板) ---
THEMES = {
    "Minimal White (极简白)": {
        "bg": "#FAFAFA",           # 全局背景
        "sidebar": "#FFFFFF",      # 侧边栏纯白
        "sidebar_fg": "#52525B",   # 侧边栏文字 (Zinc-600)
        "card_bg": "#FFFFFF",      # 卡片背景
        "fg": "#18181B",           # 主文字 (Zinc-900)
        "fg_dim": "#A1A1AA",       # 次级文字 (Zinc-400)
        "input_bg": "#F4F4F5",     # 输入框 (Zinc-100)
        "input_fg": "#18181B",
        "border": "#E4E4E7",       # 边框 (Zinc-200)
        "primary": "#2563EB",      # 品牌蓝 (Blue-600)
        "primary_fg": "#FFFFFF",
        "accent": "#EFF6FF",       # 强调背景 (Blue-50)
        "success": "#10B981",      # Emerald-500
        "warning": "#F59E0B",      # Amber-500
        "danger": "#EF4444",       # Red-500
        "select_bg": "#DBEAFE",    # 列表选中
        "select_fg": "#1E3A8A"
    },
    "Midnight Pro (深空灰)": {
        "bg": "#09090B",           # Zinc-950
        "sidebar": "#18181B",      # Zinc-900
        "sidebar_fg": "#A1A1AA",
        "card_bg": "#18181B",
        "fg": "#F4F4F5",           # Zinc-100
        "fg_dim": "#71717A",       # Zinc-500
        "input_bg": "#27272A",     # Zinc-800
        "input_fg": "#FFFFFF",
        "border": "#27272A",
        "primary": "#3B82F6",      # Blue-500
        "primary_fg": "#FFFFFF",
        "accent": "#1E293B",       # Slate-800
        "success": "#34D399",
        "warning": "#FBBF24",
        "danger": "#F87171",
        "select_bg": "#172554",
        "select_fg": "#93C5FD"
    }
}

class FileRenamerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Rename Pro")
        self.root.geometry("1100x850")
        self.root.minsize(900, 700)
        
        # --- 字体适配 (更精致的字体栈) ---
        system_name = platform.system()
        self.is_mac = system_name == "Darwin"
        
        if self.is_mac:
            # macOS 原生字体栈
            self.fonts = {
                "h1": ("SF Pro Display", 20, "bold"),
                "h2": ("SF Pro Text", 13, "bold"),
                "body": ("SF Pro Text", 12),
                "small": ("SF Pro Text", 11),
                "mono": ("SF Mono", 11)
            }
            self.row_height = 36
        else:
            # Windows/Linux 字体栈 (Segoe UI / Microsoft YaHei)
            self.fonts = {
                "h1": ("Segoe UI Variable Display", 18, "bold"),
                "h2": ("Segoe UI", 11, "bold"),
                "body": ("Segoe UI", 10),
                "small": ("Segoe UI", 9),
                "mono": ("Consolas", 10)
            }
            self.row_height = 34

        # 核心变量
        self.all_iids = []
        self.target_folder = ""
        self.api_key_var = tk.StringVar()
        self.model_var = tk.StringVar(value="Qwen/Qwen2.5-7B-Instruct")
        self.service_var = tk.StringVar(value="google")
        self.rule_var = tk.StringVar(value="纯英文 (English Only)")
        self.recursive_var = tk.BooleanVar(value=False)
        self.audio_only_var = tk.BooleanVar(value=False)
        self.theme_var = tk.StringVar(value="Minimal White (极简白)") 
        self.filter_error_var = tk.BooleanVar(value=False)
        self.mode_var = tk.StringVar(value="translate")
        self.stop_event = threading.Event()
        self.completed_count = 0 # 任务完成计数器

        # UI 组件引用 (用于动态更新)
        self.nav_btns = {}
        self.status_indicators = {}

        # 加载配置
        self.load_config()
        self.init_vars()
        
        # 应用当前主题颜色
        self.colors = THEMES.get(self.theme_var.get(), THEMES["Minimal White (极简白)"])
        
        # --- 构建 UI ---
        self.setup_styles()
        self.build_ui()
        
        # 延迟加载上次文件夹
        if self.target_folder and os.path.exists(self.target_folder):
            self.root.after(200, self.load_files)

    def setup_styles(self):
        """配置 ttk 样式"""
        self.style = ttk.Style()
        try:
            self.style.theme_use('clam')
        except:
            pass
        
        c = self.colors
        
        # 全局背景
        self.root.configure(bg=c["bg"])
        self.style.configure(".", background=c["bg"], foreground=c["fg"], font=self.fonts["body"])
        
        # Treeview (更现代的表格)
        self.style.configure("Treeview", 
                             background=c["card_bg"], 
                             foreground=c["fg"], 
                             fieldbackground=c["card_bg"], 
                             rowheight=self.row_height, 
                             borderwidth=0,
                             font=self.fonts["mono"]) # 使用等宽字体对齐文件名
        
        self.style.configure("Treeview.Heading", 
                             background=c["bg"], 
                             foreground=c["fg_dim"], 
                             font=self.fonts["small"], 
                             relief="flat")
        
        self.style.map('Treeview', 
                       background=[('selected', c['select_bg'])], 
                       foreground=[('selected', c['select_fg'])])
        
        # TFrame 变体
        self.style.configure("Card.TFrame", background=c["card_bg"])
        self.style.configure("Sidebar.TFrame", background=c["sidebar"])
        self.style.configure("Content.TFrame", background=c["bg"])
        
        # 现代化的 Combobox
        self.style.configure("TCombobox", 
                             fieldbackground=c["input_bg"], 
                             background=c["input_bg"], 
                             foreground=c["fg"],
                             arrowcolor=c["fg"],
                             borderwidth=0)
        self.style.map('TCombobox', fieldbackground=[('readonly', c['input_bg'])],
                                    selectbackground=[('readonly', c['input_bg'])],
                                    selectforeground=[('readonly', c['fg'])])

        # Mac 专属优化：去除 Treeview 边框线
        self.style.layout("Treeview", [('Treeview.treearea', {'sticky': 'nswe'})])

    def change_theme(self, event=None):
        """无缝切换主题"""
        new_theme = self.theme_var.get()
        if new_theme not in THEMES: return
        self.colors = THEMES[new_theme]
        
        self.setup_styles()
        
        # 重绘所有界面
        for widget in self.root.winfo_children():
            widget.destroy()
        self.build_ui()
        self.save_config()
        
        if self.target_folder:
             self.load_files()

    def build_ui(self):
        """构建现代布局"""
        c = self.colors
        
        # --- 0. 系统菜单 (Mac 必备) ---
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="📂 打开文件夹...", command=self.select_folder)
        menubar.add_cascade(label="文件", menu=file_menu)
        self.root.config(menu=menubar)

        # --- 1. 左侧导航栏 (Sidebar) ---
        sidebar = ttk.Frame(self.root, style="Sidebar.TFrame", width=260)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        
        # App Header
        header_frame = tk.Frame(sidebar, bg=c["sidebar"], height=80)
        header_frame.pack(fill="x", padx=24, pady=30)
        tk.Label(header_frame, text="Smart Rename", bg=c["sidebar"], fg=c["primary"], font=self.fonts["h1"], anchor="w").pack(fill="x")
        tk.Label(header_frame, text="批量文件处理工具", bg=c["sidebar"], fg=c["fg_dim"], font=self.fonts["small"], anchor="w").pack(fill="x")

        # 文件夹信息卡片
        folder_card = tk.Frame(sidebar, bg=c["input_bg"], padx=15, pady=15)
        folder_card.pack(fill="x", padx=20, pady=(0, 20))
        
        tk.Label(folder_card, text="当前工作区", bg=c["input_bg"], fg=c["fg_dim"], font=self.fonts["small"]).pack(anchor="w")
        
        # 路径显示
        path_text = os.path.basename(self.target_folder) if self.target_folder else "未选择文件夹"
        self.lbl_path = tk.Label(folder_card, text=path_text, bg=c["input_bg"], fg=c["fg"], font=self.fonts["h2"], anchor="w", cursor="hand2")
        self.lbl_path.pack(fill="x", pady=(5, 10))
        self.lbl_path.bind("<Button-1>", lambda e: self.select_folder())
        
        # 更现代的按钮 (Mac 兼容)
        if self.is_mac:
            # Mac 使用 ttk.Button 保证可见性
            btn_change = ttk.Button(folder_card, text="📂 切换目录", command=self.select_folder)
        else:
            # Windows 使用自定义扁平按钮
            btn_change = self.create_button(folder_card, "📂 切换目录", self.select_folder, bg=c["bg"], fg=c["fg"], border=1, b_color=c["border"])
        btn_change.pack(fill="x")

        # 导航菜单
        nav_container = tk.Frame(sidebar, bg=c["sidebar"])
        nav_container.pack(fill="x", padx=10)
        
        tk.Label(nav_container, text="模式", bg=c["sidebar"], fg=c["fg_dim"], font=self.fonts["small"]).pack(anchor="w", padx=14, pady=(10,5))
        self.create_nav_item(nav_container, "✨ 智能翻译模式", "translate").pack(fill="x", pady=2)
        self.create_nav_item(nav_container, "🛠️ 批量工具箱", "tools").pack(fill="x", pady=2)
        
        # 底部设置区
        bottom_frame = tk.Frame(sidebar, bg=c["sidebar"], pady=20)
        bottom_frame.pack(side="bottom", fill="x", padx=20)
        
        tk.Label(bottom_frame, text="选项", bg=c["sidebar"], fg=c["fg_dim"], font=self.fonts["small"]).pack(anchor="w", pady=(0,5))
        
        self.create_check(bottom_frame, "递归子目录", self.recursive_var, self.reload_files_if_ready).pack(fill="x", pady=2)
        self.create_check(bottom_frame, "仅音频文件", self.audio_only_var, self.reload_files_if_ready).pack(fill="x", pady=2)
        
        tk.Label(bottom_frame, text="主题", bg=c["sidebar"], fg=c["fg_dim"], font=self.fonts["small"]).pack(anchor="w", pady=(15,5))
        theme_cb = ttk.Combobox(bottom_frame, textvariable=self.theme_var, values=list(THEMES.keys()), state="readonly")
        theme_cb.pack(fill="x")
        theme_cb.bind("<<ComboboxSelected>>", self.change_theme)

        # --- 2. 主内容区 (Main) ---
        main_area = ttk.Frame(self.root, style="Content.TFrame")
        main_area.pack(side="right", fill="both", expand=True)
        
        # 顶部动态配置栏 (Header)
        self.header_panel = tk.Frame(main_area, bg=c["bg"], height=80)
        self.header_panel.pack(fill="x", padx=30, pady=30)
        self.update_header_panel() # 动态加载内容
        
        # 文件列表容器 (Card)
        list_card = tk.Frame(main_area, bg=c["card_bg"])
        list_card.pack(fill="both", expand=True, padx=30, pady=(0, 30))
        
        # 列表工具栏
        toolbar = tk.Frame(list_card, bg=c["card_bg"], pady=15, padx=20)
        toolbar.pack(fill="x")
        
        tk.Label(toolbar, text="预览列表", bg=c["card_bg"], fg=c["fg"], font=self.fonts["h2"]).pack(side="left")
        
        # 筛选器
        filter_frame = tk.Frame(toolbar, bg=c["card_bg"])
        filter_frame.pack(side="right")
        self.create_check(filter_frame, "⚠️ 只看错误项", self.filter_error_var, self.apply_filter, bg=c["card_bg"]).pack(side="right")

        # 分割线
        tk.Frame(list_card, bg=c["border"], height=1).pack(fill="x")

        # 列表本身
        tree_frame = tk.Frame(list_card, bg=c["card_bg"])
        tree_frame.pack(fill="both", expand=True, padx=1, pady=1)
        
        columns = ("status", "original", "translated")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", style="Treeview")
        
        self.tree.heading("status", text="状态", anchor="center")
        self.tree.heading("original", text="原始文件名 (支持相对路径)", anchor="w")
        self.tree.heading("translated", text="新文件名预览", anchor="w")
        
        self.tree.column("status", width=80, anchor="center")
        self.tree.column("original", width=380)
        self.tree.column("translated", width=380)
        
        # 滚动条 (隐形风格)
        sb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=sb.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        
        self.tree.bind("<Double-1>", self.on_double_click)
        self.tree.bind("<Button-3>", self.show_context_menu)
        
        # 底部栏 (Action Bar)
        action_bar = tk.Frame(main_area, bg=c["bg"], pady=10, padx=30)
        action_bar.pack(side="bottom", fill="x", pady=(0, 20))
        
        # 状态指示
        self.status_label = tk.Label(action_bar, text="准备就绪", bg=c["bg"], fg=c["fg_dim"], font=self.fonts["small"])
        self.status_label.pack(side="left")
        
        self.progress = ttk.Progressbar(action_bar, orient="horizontal", length=250, mode="determinate")
        self.progress.pack(side="left", padx=20)
        
        # 执行按钮 (最醒目)
        self.btn_run = self.create_button(action_bar, "🚀 开始重命名", self.apply_rename, 
                                          bg=c["success"], fg="#ffffff", font_size=11, bold=True, state="disabled", width=16)
        self.btn_run.pack(side="right")

        # 右键菜单
        self.context_menu = Menu(self.root, tearoff=0, bg=c["card_bg"], fg=c["fg"], bd=0)
        self.context_menu.add_command(label="✏️ 手动修改名称", command=self.manual_edit_selected)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="↩️ 还原为原名", command=self.reset_selected)
        self.context_menu.add_command(label="🔄 仅重试此项翻译", command=self.retry_selected_translation)

    def create_nav_item(self, parent, text, mode_val):
        """创建侧边栏胶囊导航按钮"""
        c = self.colors
        
        def on_click(e=None):
            self.mode_var.set(mode_val)
            self.refresh_nav_state()
            self.update_header_panel()

        # 使用 Label 模拟按钮以获得更好的样式控制 (hover, padding, rounded feel)
        btn = tk.Label(parent, text=text, font=self.fonts["body"], anchor="w",
                       bg=c["sidebar"], fg=c["sidebar_fg"], padx=15, pady=10, cursor="hand2")
        
        # 绑定事件
        btn.bind("<Button-1>", on_click)
        btn.bind("<Enter>", lambda e: btn.config(bg=c["input_bg"]) if self.mode_var.get() != mode_val else None)
        btn.bind("<Leave>", lambda e: btn.config(bg=c["sidebar"]) if self.mode_var.get() != mode_val else None)
        
        self.nav_btns[mode_val] = btn
        
        # 初始化状态
        if self.mode_var.get() == mode_val:
            btn.config(bg=c["accent"], fg=c["primary"], font=self.fonts["h2"])
            
        return btn

    def refresh_nav_state(self):
        c = self.colors
        curr = self.mode_var.get()
        for mode, btn in self.nav_btns.items():
            if mode == curr:
                btn.config(bg=c["accent"], fg=c["primary"], font=self.fonts["h2"])
            else:
                btn.config(bg=c["sidebar"], fg=c["sidebar_fg"], font=self.fonts["body"])

    def update_header_panel(self):
        """根据模式渲染顶部配置区域"""
        for w in self.header_panel.winfo_children(): w.destroy()
        c = self.colors
        mode = self.mode_var.get()
        
        # 标题行
        title_row = tk.Frame(self.header_panel, bg=c["bg"])
        title_row.pack(fill="x", pady=(0, 15))
        
        title_txt = "AI 智能翻译配置" if mode == "translate" else "批量工具箱"
        tk.Label(title_row, text=title_txt, bg=c["bg"], fg=c["fg"], font=self.fonts["h1"]).pack(side="left")
        
        # 内容行
        content_row = tk.Frame(self.header_panel, bg=c["bg"])
        content_row.pack(fill="x")
        
        if mode == "translate":
            # 翻译控制
            self.create_combo(content_row, "引擎", self.service_var, ["google", "silicon"], width=8).pack(side="left", padx=(0, 15))
            self.create_combo(content_row, "命名格式", self.rule_var, ["纯英文 (English Only)", "纯中文 (Chinese Only)", "英文_中文", "中文_英文"], width=20).pack(side="left", padx=0)
            
            # 操作按钮
            btn_frame = tk.Frame(content_row, bg=c["bg"])
            btn_frame.pack(side="right")
            
            self.btn_preview = self.create_button(btn_frame, "⚡ 生成/刷新预览", self.start_translation_thread, bg=c["primary"], fg=c["primary_fg"])
            self.btn_preview.pack(side="left", padx=10)
            
            self.btn_stop = self.create_button(btn_frame, "🛑", self.stop_translation, bg=c["danger"], fg="#fff", width=3, state="disabled")
            self.btn_stop.pack(side="left")
            
            # 动态 AI 设置
            self.ai_settings_container = tk.Frame(self.header_panel, bg=c["bg"])
            self.ai_settings_container.pack(fill="x", pady=10)
            self.render_ai_settings()
            
            # 监听引擎变化
            self.service_var.trace_add("write", lambda *args: self.render_ai_settings())

        elif mode == "tools":
            # 工具箱控制 (网格布局)
            grid = tk.Frame(content_row, bg=c["bg"])
            grid.pack(fill="x")
            
            # 辅助函数：快速创建工具行
            def tool_item(p, icon, label, input_ui_func, cmd):
                f = tk.Frame(p, bg=c["card_bg"], padx=10, pady=8, highlightbackground=c["border"], highlightthickness=1)
                f.pack(side="left", padx=(0, 15), fill="y")
                
                head = tk.Frame(f, bg=c["card_bg"])
                head.pack(fill="x", pady=(0,5))
                tk.Label(head, text=icon, bg=c["card_bg"], font=("Arial", 12)).pack(side="left")
                tk.Label(head, text=label, bg=c["card_bg"], fg=c["fg_dim"], font=self.fonts["small"]).pack(side="left", padx=5)
                
                body = tk.Frame(f, bg=c["card_bg"])
                body.pack(fill="x")
                input_ui_func(body)
                self.create_button(body, "Go", cmd, bg=c["input_bg"], fg=c["fg"], border=1, b_color=c["border"], width=3, font_size=8).pack(side="right", padx=(5,0))

            # 工具 1: 替换
            tool_item(grid, "🔄", "文本替换", 
                      lambda p: (self.create_entry(p, self.ent_find, 6).pack(side="left"), 
                                 tk.Label(p, text="→", bg=c["card_bg"], fg=c["fg_dim"]).pack(side="left", padx=2),
                                 self.create_entry(p, self.ent_rep, 6).pack(side="left")),
                      self.tool_replace)
            
            # 工具 2: 前后缀
            tool_item(grid, "🔤", "添加字符", 
                      lambda p: (self.create_entry(p, self.ent_prefix, 6).pack(side="left"), 
                                 tk.Label(p, text="+", bg=c["card_bg"], fg=c["fg_dim"]).pack(side="left", padx=2),
                                 self.create_entry(p, self.ent_suffix, 6).pack(side="left")),
                      self.tool_add_fix)
            
            # 工具 3: 序号
            tool_item(grid, "🔢", "自动序号", 
                      lambda p: (self.create_entry(p, self.ent_seq_name, 6).pack(side="left"), 
                                 tk.Label(p, text="#", bg=c["card_bg"], fg=c["fg_dim"]).pack(side="left", padx=2),
                                 self.create_entry(p, self.ent_seq_start, 3).pack(side="left")),
                      self.tool_sequence)

    def render_ai_settings(self):
        """渲染 AI 专属设置行"""
        for w in self.ai_settings_container.winfo_children(): w.destroy()
        c = self.colors
        if self.service_var.get() == "silicon":
            row = tk.Frame(self.ai_settings_container, bg=c["bg"])
            row.pack(fill="x")
            
            tk.Label(row, text="🔑 API Key", bg=c["bg"], fg=c["fg_dim"], font=self.fonts["small"]).pack(side="left")
            self.create_entry(row, self.api_key_var, width=25, show="*").pack(side="left", padx=(5, 15))
            
            tk.Label(row, text="🤖 模型", bg=c["bg"], fg=c["fg_dim"], font=self.fonts["small"]).pack(side="left")
            
            # 关键修复：将 Combobox 赋值给 self.combo_model，以便 fetch_silicon_models 能访问并更新它
            self.combo_model = ttk.Combobox(row, textvariable=self.model_var, width=25)
            self.combo_model.pack(side="left", padx=5)
            
            self.create_button(row, "⟳", self.fetch_silicon_models, bg=c["input_bg"], fg=c["fg"], border=1, b_color=c["border"], width=3).pack(side="left")

    # --- UI 基础组件工厂 ---
    def create_button(self, parent, text, command, bg, fg, width=None, font_size=10, bold=False, state="normal", border=0, b_color=None):
        """创建扁平化按钮 (Windows 模拟边框, Mac 原生适配)"""
        f_font = (self.fonts["body"][0], font_size, "bold" if bold else "normal")
        
        # 容器 Frame (用于边框或 padding)
        frame = tk.Frame(parent, bg=b_color if border > 0 else bg, padx=border, pady=border)
        
        btn = tk.Button(frame, text=text, command=command, 
                        bg=bg, fg=fg, 
                        font=f_font, width=width, 
                        relief="flat", bd=0, 
                        activebackground=bg, activeforeground=fg,
                        state=state, cursor="hand2")
        btn.pack(fill="both", expand=True)
        
        # 关键修复：将按钮实例附加到 Frame 上，方便外部调用 config 修改状态
        frame.btn = btn 
        
        return frame

    def create_entry(self, parent, var, width=None, show=None):
        """创建带下划线或边框的输入框"""
        c = self.colors
        # 包裹层
        frame = tk.Frame(parent, bg=c["input_bg"], highlightbackground=c["border"], highlightthickness=1, padx=5, pady=3)
        entry = tk.Entry(frame, textvariable=var, width=width, show=show,
                         bg=c["input_bg"], fg=c["input_fg"],
                         insertbackground=c["fg"], relief="flat", font=self.fonts["body"])
        entry.pack(fill="both", expand=True)
        return frame

    def create_combo(self, parent, label, var, values, width=10):
        """带标签的下拉框"""
        c = self.colors
        f = tk.Frame(parent, bg=c["bg"])
        tk.Label(f, text=label, bg=c["bg"], fg=c["fg_dim"], font=self.fonts["small"]).pack(anchor="w")
        cb = ttk.Combobox(f, textvariable=var, values=values, state="readonly", width=width)
        cb.pack(fill="x", pady=(2,0))
        return f

    def create_check(self, parent, text, var, command, bg=None):
        c = self.colors
        actual_bg = bg if bg else c["sidebar"]
        cb = tk.Checkbutton(parent, text=text, variable=var, command=command,
                            bg=actual_bg, fg=c["fg"], selectcolor=actual_bg,
                            activebackground=actual_bg, activeforeground=c["fg"],
                            font=self.fonts["body"], cursor="hand2")
        return cb

    # --- 变量初始化 ---
    def init_vars(self):
        self.ent_find = tk.StringVar()
        self.ent_rep = tk.StringVar()
        self.ent_prefix = tk.StringVar()
        self.ent_suffix = tk.StringVar()
        self.ent_seq_name = tk.StringVar(value="file")
        self.ent_seq_start = tk.StringVar(value="1")

    # --- 核心逻辑 (保持不变) ---
    def select_folder(self):
        initial = self.target_folder if os.path.exists(self.target_folder) else "/"
        folder_selected = filedialog.askdirectory(initialdir=initial)
        if folder_selected:
            self.target_folder = folder_selected
            if hasattr(self, 'lbl_path'):
                self.lbl_path.config(text=os.path.basename(folder_selected))
            self.save_config()
            self.load_files()

    def reload_files_if_ready(self):
        if self.target_folder and os.path.exists(self.target_folder):
            self.load_files()

    def load_files(self):
        for item in self.tree.get_children(): self.tree.delete(item)
        self.all_iids = []
        
        # 修复：使用 .btn 访问内部按钮进行状态配置
        self.btn_run.btn.config(state="disabled") 
        
        self.status_label.config(text="正在扫描文件...")
        self.root.update()

        files_found = []
        try:
            recursive = self.recursive_var.get()
            audio_only = self.audio_only_var.get()
            
            if recursive:
                for root, dirs, files in os.walk(self.target_folder):
                    for f in files:
                        if f.startswith('.'): continue
                        if audio_only and os.path.splitext(f)[1].lower() not in AUDIO_EXTENSIONS: continue
                        full_path = os.path.join(root, f)
                        rel_path = os.path.relpath(full_path, self.target_folder)
                        files_found.append(rel_path)
            else:
                for f in os.listdir(self.target_folder):
                    if f.startswith('.'): continue
                    if os.path.isfile(os.path.join(self.target_folder, f)):
                        if audio_only and os.path.splitext(f)[1].lower() not in AUDIO_EXTENSIONS: continue
                        files_found.append(f)
            
            files_found.sort()
            for f in files_found:
                iid = self.tree.insert("", "end", values=("待处理", f, f))
                self.all_iids.append(iid)
            
            self.status_label.config(text=f"已加载 {len(files_found)} 个文件")
            if files_found: 
                # 修复：使用 .btn 访问
                self.btn_run.btn.config(state="normal")
            
            if self.filter_error_var.get():
                self.apply_filter()
                
        except Exception as e:
            messagebox.showerror("错误", str(e))

    # --- 翻译逻辑 ---
    def start_translation_thread(self):
        if not self.target_folder: 
            messagebox.showinfo("提示", "请先选择文件夹")
            return
        service = self.service_var.get()
        if service == "silicon":
            if not self.api_key_var.get().strip():
                messagebox.showwarning("提示", "请输入 API Key")
                return
            self.save_config()

        # 修复：使用 .btn 访问
        self.btn_preview.btn.config(state="disabled") 
        self.btn_stop.btn.config(state="normal")
        
        self.stop_event.clear()
        
        visible_items = self.tree.get_children()
        self.progress['maximum'] = len(visible_items)
        self.progress['value'] = 0
        self.completed_count = 0  # 重置计数器
        
        threading.Thread(target=self.perform_translation, args=(visible_items,), daemon=True).start()

    def perform_translation(self, items):
        service = self.service_var.get()
        rule = self.rule_var.get()
        api_key = self.api_key_var.get().strip()
        model = self.model_var.get().strip()
        
        # --- 核心修改：根据服务类型动态调整并发数 ---
        if service == "silicon":
            # AI 模式：强制单线程
            max_threads = 1
            # 修复：针对未验证账户的 RPM 限制，大幅增加间隔 (10~15秒/次，约 <4 RPM)
            # 虽然慢，但能避免报错中断
            delay_min, delay_max = 10.0, 15.0 
        else:
            # Google 模式：多线程并发，追求速度
            max_threads = 8 
            delay_min, delay_max = 0.05, 0.1

        # 预取数据以在线程池中使用
        tasks = []
        for item_id in items:
            vals = self.tree.item(item_id)['values']
            if not vals: continue
            tasks.append((item_id, vals[1])) # (id, original_rel_path)

        def worker(item_id, original_rel):
            if self.stop_event.is_set(): return None
            
            # 应用动态延时
            time.sleep(random.uniform(delay_min, delay_max))
            
            dirname, filename = os.path.split(original_rel)
            name, ext = os.path.splitext(filename)
            
            try:
                # 线程内实例化
                translator_en = GoogleTranslator(source='auto', target='en')
                translator_zh = GoogleTranslator(source='auto', target='zh-CN')

                def get_trans(code, desc):
                    if service == "silicon":
                        return self.call_silicon_ai(name, desc, api_key, model)
                    return translator_en.translate(name) if code == "en" else translator_zh.translate(name)

                final = ""
                if "纯英文" in rule: final = self.clean_text(get_trans("en", "English"))
                elif "纯中文" in rule: final = self.clean_text(get_trans("zh", "Chinese"))
                elif "英文_中文" in rule: final = f"{self.clean_text(get_trans('en','English'))}_{self.clean_text(get_trans('zh','Chinese'))}"
                elif "中文_英文" in rule: final = f"{self.clean_text(get_trans('zh','Chinese'))}_{self.clean_text(get_trans('en','English'))}"
                
                new_rel = os.path.join(dirname, final + ext)
                return (item_id, new_rel, "预览")
            except Exception as e:
                # 这里可以打印具体的错误信息到控制台，方便调试
                print(f"Translation error for {filename}: {e}")
                return (item_id, original_rel, "失败")

        # 使用线程池并发 (并发数由 max_threads 变量控制)
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
            # 提交任务
            future_to_item = {executor.submit(worker, iid, txt): iid for iid, txt in tasks}
            
            for future in concurrent.futures.as_completed(future_to_item):
                if self.stop_event.is_set():
                    executor.shutdown(wait=False, cancel_futures=True)
                    break
                
                try:
                    result = future.result()
                    if result:
                        iid, new_val, status = result
                        # UI 更新必须在主线程
                        self.root.after(0, lambda i=iid, n=new_val, s=status: self.update_item_result(i, n, s))
                except:
                    pass
                
                # 进度更新
                self.completed_count += 1
                self.root.after(0, lambda v=self.completed_count: self.progress.configure(value=v))

        self.root.after(0, self.finish_translation)

    def update_item_result(self, item_id, new_val, status):
        """辅助方法：安全更新 Treeview"""
        current_vals = self.tree.item(item_id)['values']
        if not current_vals: return
        
        if status == "失败":
             self.tree.item(item_id, values=("失败", current_vals[1], "错误"))
        else:
             self.tree.item(item_id, values=("预览", current_vals[1], new_val))

    def finish_translation(self):
        # 修复：使用 .btn 访问
        self.btn_preview.btn.config(state="normal")
        self.btn_stop.btn.config(state="disabled")
        
        self.status_label.config(text="预览生成完毕，请检查列表")
        if self.filter_error_var.get():
             self.root.after(0, self.apply_filter)

    def stop_translation(self):
        self.stop_event.set()
        self.status_label.config(text="正在停止...")

    # --- 批量工具逻辑 ---
    def _apply_tool_logic(self, func):
        if not self.target_folder: return
        count = 0
        items = self.tree.get_children()
        for item in items:
            vals = self.tree.item(item)['values']
            curr_rel = vals[2]
            if "错误" in curr_rel: continue
            
            dirname, filename = os.path.split(curr_rel)
            new_name = func(filename, count)
            if new_name:
                self.tree.item(item, values=("预览", vals[1], os.path.join(dirname, new_name)))
                count += 1
        self.status_label.config(text=f"应用完成，更新了 {count} 个文件")

    def tool_replace(self):
        f, r = self.ent_find.get(), self.ent_rep.get()
        if f: self._apply_tool_logic(lambda n, c: n.replace(f, r))

    def tool_add_fix(self):
        p, s = self.ent_prefix.get(), self.ent_suffix.get()
        def logic(n, c):
            name, ext = os.path.splitext(n)
            return f"{p}{name}{s}{ext}"
        self._apply_tool_logic(logic)

    def tool_sequence(self):
        base, start_str = self.ent_seq_name.get(), self.ent_seq_start.get()
        try: start = int(start_str) 
        except: start = 1
        def logic(n, c):
            name, ext = os.path.splitext(n)
            return f"{base}_{str(start + c).zfill(3)}{ext}"
        self._apply_tool_logic(logic)

    # --- 辅助功能 ---
    def clean_text(self, text):
        if not text: return ""
        s = text.lower().replace(" ", "_")
        for c in "/\\:*?\"<>|'’": s = s.replace(c, "")
        return s.strip("_")

    def call_silicon_ai(self, text, lang, key, model):
        url = "https://api.siliconflow.cn/v1/chat/completions"
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        
        # 修复：升级系统提示词，强制AI遵守格式，防止"话痨"
        system_prompt = "You are a professional filename translator. You must return ONLY the translated text. Do not include the original file extension. Do not add notes, explanations, or punctuation."
        user_prompt = f"Translate this filename to {lang}: \"{text}\""
        
        data = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.3
        }
        
        # 修复：增加自动重试机制，应对 403/429 速率限制
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # 延长超时时间到 30 秒，防止 Read timed out
                res = requests.post(url, json=data, headers=headers, timeout=30)
                
                # 如果成功，直接处理
                if res.status_code == 200:
                    try:
                        result_json = res.json()
                    except:
                        raise Exception(f"无法解析响应数据: {res.text}")

                    if not isinstance(result_json, dict) or 'choices' not in result_json:
                        raise Exception(f"API 返回格式异常: {str(result_json)}")
                        
                    content = result_json['choices'][0]['message']['content'].strip()
                    # 修复：结果清洗，去除可能存在的引号、代码块符号等
                    content = content.replace('"', '').replace("'", "").replace("`", "")
                    return content
                
                # 如果是速率限制 (403 RPM limit 或 429 Too Many Requests)，等待后重试
                elif res.status_code in [403, 429]:
                    if attempt < max_retries - 1:
                        # 修复：大幅增加等待时间，因为 RPM 限制通常需要等待较长时间才能解除
                        wait_time = (attempt + 1) * 10  # 第一次等10秒，第二次等20秒...
                        print(f"触发速率限制 (HTTP {res.status_code})，等待 {wait_time} 秒后重试...")
                        time.sleep(wait_time)
                        continue
                    else:
                        # 重试次数用尽，尝试解析错误信息
                        try:
                            err_msg = res.json().get('message', res.text)
                        except:
                            err_msg = res.text
                        raise Exception(f"速率限制重试失败: {err_msg}")
                
                else:
                    # 其他错误 (500, 401等)
                    raise Exception(f"API请求失败 (HTTP {res.status_code}): {res.text}")

            except requests.exceptions.RequestException as e:
                # 网络层面错误，也进行重试
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                raise Exception(f"网络连接错误: {str(e)}")

    def fetch_silicon_models(self):
        key = self.api_key_var.get().strip()
        if not key: return messagebox.showerror("Error", "Need API Key")
        def run():
            try:
                res = requests.get("https://api.siliconflow.cn/v1/models", headers={"Authorization": f"Bearer {key}"})
                all_models = sorted([i['id'] for i in res.json().get('data', [])])
                
                # 核心修复：自动过滤掉 Embedding 和 Reranker 模型，只保留对话模型
                # BAAI/bge... 是典型的 embedding 模型，不能用于对话
                chat_models = [m for m in all_models if "bge" not in m and "embedding" not in m and "reranker" not in m]
                
                # 万一全被过滤了，就回退到显示所有
                if not chat_models: chat_models = all_models

                def update_ui():
                    # 检查 combobox 是否存在
                    if hasattr(self, 'combo_model'):
                        self.combo_model['values'] = chat_models
                        if chat_models:
                            # 只有当前选中的不在列表里时才重置
                            current = self.model_var.get()
                            if current not in chat_models:
                                self.model_var.set(chat_models[0])
                    messagebox.showinfo("OK", f"已刷新，获取到 {len(chat_models)} 个可用模型")
                
                self.root.after(0, update_ui)
            except Exception as e:
                err_msg = str(e)
                self.root.after(0, lambda: messagebox.showerror("Error", err_msg))
        threading.Thread(target=run, daemon=True).start()

    def apply_filter(self):
        show_error_only = self.filter_error_var.get()
        for iid in self.all_iids:
            vals = self.tree.item(iid)['values']
            if not vals: continue
            status = str(vals[0])
            is_error = "失败" in status or "错误" in status or "出错" in status
            if show_error_only:
                if is_error: self.tree.move(iid, '', 'end')
                else: self.tree.detach(iid)
            else:
                self.tree.move(iid, '', 'end')

    def apply_rename(self):
        if not messagebox.askyesno("确认", "确定执行重命名操作吗？此操作不可撤销。"): return
        success = 0
        items = self.tree.get_children()
        for item in items:
            vals = self.tree.item(item)['values']
            old_rel, new_rel = vals[1], vals[2]
            if "错误" in new_rel or old_rel == new_rel: continue
            try:
                os.makedirs(os.path.dirname(os.path.join(self.target_folder, new_rel)), exist_ok=True)
                os.rename(os.path.join(self.target_folder, old_rel), os.path.join(self.target_folder, new_rel))
                self.tree.item(item, values=("完成", old_rel, new_rel))
                success += 1
            except Exception as e:
                self.tree.item(item, values=("错误", old_rel, str(e)))
        messagebox.showinfo("完成", f"成功重命名 {success} 个文件")
        self.load_files()

    def on_double_click(self, event): self.manual_edit_selected()
    def show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
    def manual_edit_selected(self):
        sel = self.tree.selection()
        if not sel: return
        vals = self.tree.item(sel[0])['values']
        res = simpledialog.askstring("编辑", "新文件名:", initialvalue=vals[2], parent=self.root)
        if res: self.tree.item(sel[0], values=("手动", vals[1], res))
    def reset_selected(self):
        for i in self.tree.selection():
            v = self.tree.item(i)['values']
            self.tree.item(i, values=("重置", v[1], v[1]))
    def retry_selected_translation(self):
        self.start_translation_thread()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    c = json.load(f)
                    self.api_key_var.set(c.get("api_key", ""))
                    self.target_folder = c.get("last_folder", "")
                    self.theme_var.set(c.get("theme", "Minimal White (极简白)"))
            except: pass

    def save_config(self):
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump({
                    "api_key": self.api_key_var.get(),
                    "last_folder": self.target_folder,
                    "theme": self.theme_var.get()
                }, f)
        except: pass

if __name__ == "__main__":
    root = tk.Tk()
    app = FileRenamerApp(root)
    root.mainloop()