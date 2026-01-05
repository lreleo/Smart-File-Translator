import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, simpledialog, Menu
import requests
import json
# 需要用户先运行: pip install deep-translator requests
from deep_translator import GoogleTranslator

# 配置文件名
CONFIG_FILE = "translator_config.json"

class FileRenamerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("智能文件名翻译 & 重命名工具 v7.0 (支持自定义模型)")
        self.root.geometry("1000x900")
        
        # 线程控制标志
        self.stop_event = threading.Event()
        
        # --- 样式美化设置 ---
        self.style = ttk.Style()
        try:
            self.style.theme_use('clam')
        except:
            pass
        
        self.colors = {
            "bg": "#f0f0f0",
            "primary": "#2196F3",
            "success": "#4CAF50",
            "warning": "#FFC107",
            "danger": "#F44336",
            "text": "#333333"
        }
        self.root.configure(bg=self.colors["bg"])
        
        self.style.configure("Treeview", rowheight=28, font=("Microsoft YaHei", 10))
        self.style.configure("Treeview.Heading", font=("Microsoft YaHei", 10, "bold"))
        self.style.map('Treeview', background=[('selected', self.colors['primary'])])
        
        self.file_list = []
        self.target_folder = ""
        
        # --- UI 布局 ---
        
        # 1. 顶部标题与选择区
        top_frame = tk.Frame(root, bg="white", pady=15, padx=20)
        top_frame.pack(fill="x")
        
        self.btn_select = tk.Button(top_frame, text="📂 选择文件夹", command=self.select_folder, 
                                    font=("Microsoft YaHei", 11), bg="#E3F2FD", relief="flat", padx=15, pady=5)
        self.btn_select.pack(side="left")
        
        self.lbl_path = tk.Label(top_frame, text="未选择文件夹 (请先点击左侧按钮)", fg="#757575", bg="white", font=("Microsoft YaHei", 10))
        self.lbl_path.pack(side="left", padx=20)

        # 2. 功能选项卡区
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="x", padx=15, pady=10)
        
        # === 选项卡 A: 智能翻译 ===
        self.tab_trans = tk.Frame(self.notebook, bg=self.colors["bg"])
        self.notebook.add(self.tab_trans, text=" ✨ 智能翻译设置 ")
        
        # A1. 翻译服务设置
        service_container = tk.LabelFrame(self.tab_trans, text="第一步：选择翻译引擎", font=("Microsoft YaHei", 10, "bold"), pady=10, padx=10, bg=self.colors["bg"])
        service_container.pack(fill="x", padx=10, pady=5)
        
        self.service_var = tk.StringVar(value="google")
        
        # Google 选项
        tk.Radiobutton(service_container, text="Google 翻译 (推荐，免费稳定)", variable=self.service_var, value="google", bg=self.colors["bg"], font=("Microsoft YaHei", 9)).grid(row=0, column=0, sticky="w", padx=10)
        
        # AI 区域容器
        frame_ai = tk.Frame(service_container, bg=self.colors["bg"])
        frame_ai.grid(row=1, column=0, sticky="w", padx=10, pady=5)
        
        # AI 第一行：选择与 Key
        row_ai_1 = tk.Frame(frame_ai, bg=self.colors["bg"])
        row_ai_1.pack(fill="x", anchor="w")
        tk.Radiobutton(row_ai_1, text="硅基流动 AI (需API Key)", variable=self.service_var, value="silicon", bg=self.colors["bg"], font=("Microsoft YaHei", 9)).pack(side="left")
        tk.Label(row_ai_1, text="Key:", bg=self.colors["bg"]).pack(side="left", padx=5)
        self.api_key_var = tk.StringVar()
        tk.Entry(row_ai_1, textvariable=self.api_key_var, width=35, show="*").pack(side="left")
        
        # AI 第二行：模型选择
        row_ai_2 = tk.Frame(frame_ai, bg=self.colors["bg"])
        row_ai_2.pack(fill="x", anchor="w", padx=25, pady=5) # 缩进对齐
        tk.Label(row_ai_2, text="模型:", bg=self.colors["bg"]).pack(side="left")
        
        self.model_var = tk.StringVar(value="Qwen/Qwen2.5-7B-Instruct") # 默认值
        self.combo_model = ttk.Combobox(row_ai_2, textvariable=self.model_var, width=35)
        self.combo_model.pack(side="left", padx=5)
        
        tk.Button(row_ai_2, text="🔄 刷新模型列表", command=self.fetch_silicon_models, bg="#E0E0E0", relief="groove", font=("Microsoft YaHei", 8)).pack(side="left", padx=5)
        
        # A2. 命名规则
        rule_frame = tk.LabelFrame(self.tab_trans, text="第二步：选择命名格式", font=("Microsoft YaHei", 10, "bold"), pady=10, padx=10, bg=self.colors["bg"])
        rule_frame.pack(fill="x", padx=10, pady=5)
        
        self.rule_var = tk.StringVar(value="纯英文 (English Only)")
        combo_rules = ttk.Combobox(rule_frame, textvariable=self.rule_var, state="readonly", width=30, font=("Microsoft YaHei", 10))
        combo_rules['values'] = ("纯英文 (English Only)", "纯中文 (Chinese Only)", "英文_中文 (English_Chinese)", "中文_英文 (Chinese_English)")
        combo_rules.pack(side="left", padx=10)
        
        # 按钮区域 (预览 + 停止)
        btn_frame = tk.Frame(rule_frame, bg=self.colors["bg"])
        btn_frame.pack(side="right", padx=10)

        self.btn_preview = tk.Button(btn_frame, text="⚡ 生成翻译预览", command=self.start_translation_thread, 
                                     bg="#FFF9C4", font=("Microsoft YaHei", 10), relief="groove", padx=15)
        self.btn_preview.pack(side="left", padx=5)

        self.btn_stop = tk.Button(btn_frame, text="🛑 停止", command=self.stop_translation, 
                                  bg="#FFCDD2", fg="#D32F2F", font=("Microsoft YaHei", 10), relief="groove", padx=10, state="disabled")
        self.btn_stop.pack(side="left", padx=5)

        # === 选项卡 B: 批量工具箱 ===
        self.tab_tools = tk.Frame(self.notebook, bg=self.colors["bg"])
        self.notebook.add(self.tab_tools, text=" 🛠️ 常用批量工具 ")
        
        tool_grid = tk.Frame(self.tab_tools, padx=10, pady=10, bg=self.colors["bg"])
        tool_grid.pack(fill="both", expand=True)
        
        def create_tool_group(parent, title, row, col):
            group = tk.LabelFrame(parent, text=title, padx=10, pady=10, bg=self.colors["bg"], font=("Microsoft YaHei", 9, "bold"))
            group.grid(row=row, column=col, sticky="ew", padx=5, pady=5)
            return group

        # 工具1: 替换
        grp_replace = create_tool_group(tool_grid, "1. 文本替换", 0, 0)
        tk.Label(grp_replace, text="将:", bg=self.colors["bg"]).pack(side="left")
        self.ent_find = tk.Entry(grp_replace, width=8); self.ent_find.pack(side="left", padx=2)
        tk.Label(grp_replace, text="变为:", bg=self.colors["bg"]).pack(side="left")
        self.ent_rep = tk.Entry(grp_replace, width=8); self.ent_rep.pack(side="left", padx=2)
        tk.Button(grp_replace, text="执行", command=self.tool_replace, bg="#E0E0E0", relief="flat").pack(side="left", padx=10)

        # 工具2: 前后缀
        grp_fix = create_tool_group(tool_grid, "2. 添加前缀/后缀", 0, 1)
        tk.Label(grp_fix, text="前:", bg=self.colors["bg"]).pack(side="left")
        self.ent_prefix = tk.Entry(grp_fix, width=8); self.ent_prefix.pack(side="left")
        tk.Label(grp_fix, text="后:", bg=self.colors["bg"]).pack(side="left")
        self.ent_suffix = tk.Entry(grp_fix, width=8); self.ent_suffix.pack(side="left")
        tk.Button(grp_fix, text="执行", command=self.tool_add_fix, bg="#E0E0E0", relief="flat").pack(side="left", padx=10)
        
        # 工具3: 序列号
        grp_seq = create_tool_group(tool_grid, "3. 自动序号 (重置文件名)", 1, 0)
        tk.Label(grp_seq, text="基名:", bg=self.colors["bg"]).pack(side="left")
        self.ent_seq_name = tk.Entry(grp_seq, width=8); self.ent_seq_name.insert(0, "file"); self.ent_seq_name.pack(side="left")
        tk.Label(grp_seq, text="起始:", bg=self.colors["bg"]).pack(side="left")
        self.ent_seq_start = tk.Entry(grp_seq, width=4); self.ent_seq_start.insert(0, "1"); self.ent_seq_start.pack(side="left")
        tk.Button(grp_seq, text="执行", command=self.tool_sequence, bg="#E0E0E0", relief="flat").pack(side="left", padx=10)

        # 工具4: 扩展名
        grp_ext = create_tool_group(tool_grid, "4. 修改扩展名", 1, 1)
        tk.Label(grp_ext, text="新后缀:", bg=self.colors["bg"]).pack(side="left")
        self.ent_ext = tk.Entry(grp_ext, width=10); self.ent_ext.pack(side="left", padx=5)
        tk.Button(grp_ext, text="执行", command=self.tool_extension, bg="#E0E0E0", relief="flat").pack(side="left", padx=10)

        # 3. 列表显示区
        list_frame = tk.Frame(root, bg=self.colors["bg"])
        list_frame.pack(fill="both", expand=True, padx=15, pady=5)
        
        tk.Label(list_frame, text="💡 小提示：双击列表可手动修改 | 右键可重试翻译", fg="#757575", bg=self.colors["bg"], font=("Microsoft YaHei", 9)).pack(anchor="w")

        columns = ("status", "original", "translated")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", style="Treeview")
        self.tree.heading("status", text="状态")
        self.tree.heading("original", text="📄 原文件名")
        self.tree.heading("translated", text="📝 新文件名预览")
        
        self.tree.column("status", width=80, anchor="center")
        self.tree.column("original", width=350)
        self.tree.column("translated", width=450)
        
        self.tree.tag_configure('odd', background='white')
        self.tree.tag_configure('even', background='#F5F5F5')
        self.tree.tag_configure('error', background='#FFEBEE', foreground='red')
        
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)
        
        self.tree.bind("<Double-1>", self.on_double_click)
        self.tree.bind("<Button-3>", self.show_context_menu)

        self.context_menu = Menu(root, tearoff=0)
        self.context_menu.add_command(label="✏️ 手动修改", command=self.manual_edit_selected)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="🔄 重试翻译", command=self.retry_selected_translation)
        self.context_menu.add_command(label="↩️ 还原原名", command=self.reset_selected)

        # 4. 底部执行区 (带进度条)
        bottom_frame = tk.Frame(root, bg="white", pady=15)
        bottom_frame.pack(fill="x")
        
        self.progress = ttk.Progressbar(bottom_frame, orient="horizontal", length=300, mode="determinate")
        self.progress.pack(side="left", padx=20)
        
        self.status_label = tk.Label(bottom_frame, text="就绪", fg=self.colors["text"], bg="white", font=("Microsoft YaHei", 9))
        self.status_label.pack(side="left", padx=5)
        
        self.btn_run = tk.Button(bottom_frame, text="🚀 确认并执行重命名", command=self.apply_rename, 
                                 font=("Microsoft YaHei", 12, "bold"), bg="#C8E6C9", fg="#2E7D32", 
                                 relief="flat", padx=20, pady=5, state="disabled")
        self.btn_run.pack(side="right", padx=20)
        
        # 初始化配置
        self.load_config()

    # --- 配置加载与保存 ---
    
    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    key = config.get("api_key", "")
                    model = config.get("silicon_model", "Qwen/Qwen2.5-7B-Instruct")
                    self.api_key_var.set(key)
                    self.model_var.set(model)
            except Exception as e:
                print(f"读取配置失败: {e}")

    def save_config(self):
        config = {
            "api_key": self.api_key_var.get().strip(),
            "silicon_model": self.model_var.get().strip()
        }
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f)
        except Exception as e:
            print(f"保存配置失败: {e}")

    # --- 新增：获取硅基流动模型列表 ---
    
    def fetch_silicon_models(self):
        api_key = self.api_key_var.get().strip()
        if not api_key:
            messagebox.showwarning("提示", "请先输入 API Key 才能获取模型列表！")
            return
            
        self.status_label.config(text="正在从硅基流动获取模型列表...")
        self.root.update_idletasks()
        
        def run_fetch():
            url = "https://api.siliconflow.cn/v1/models"
            headers = {"Authorization": f"Bearer {api_key}"}
            
            try:
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                # 提取模型 ID 列表
                models = [item['id'] for item in data.get('data', [])]
                # 简单按字母排序
                models.sort()
                
                # 在主线程更新 UI
                self.root.after(0, lambda: self.update_model_list(models))
                
            except Exception as e:
                error_msg = str(e)
                self.root.after(0, lambda: messagebox.showerror("获取失败", f"无法获取模型列表: {error_msg}\n请检查 Key 是否正确或网络连接。"))
                self.root.after(0, lambda: self.status_label.config(text="获取模型列表失败"))

        threading.Thread(target=run_fetch, daemon=True).start()

    def update_model_list(self, models):
        if not models:
            messagebox.showinfo("提示", "API 返回的模型列表为空。")
            return
            
        self.combo_model['values'] = models
        self.status_label.config(text=f"成功获取 {len(models)} 个模型！")
        
        # 如果当前选中的模型不在列表里，默认选第一个；如果在，保持不变
        current = self.model_var.get()
        if current not in models:
            self.combo_model.current(0)
            
        # 自动展开下拉列表 (可选)
        # self.combo_model.event_generate('<Button-1>') 
        messagebox.showinfo("成功", f"成功刷新模型列表，共找到 {len(models)} 个模型。\n请在下拉框中选择。")

    # --- 核心逻辑 ---

    def select_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.target_folder = folder_selected
            self.lbl_path.config(text=folder_selected, fg="black")
            self.load_files()

    def load_files(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.file_list = []
        self.btn_run.config(state="disabled")
        self.progress['value'] = 0
        self.status_label.config(text="就绪")
        
        try:
            files = [f for f in os.listdir(self.target_folder) if os.path.isfile(os.path.join(self.target_folder, f))]
            files = [f for f in files if not f.startswith('.')]
            files.sort()
            
            for i, f in enumerate(files):
                tag = 'even' if i % 2 == 0 else 'odd'
                self.tree.insert("", "end", values=("待处理", f, f), tags=(tag,))
            
            self.status_label.config(text=f"已加载 {len(files)} 个文件，请选择功能开始操作")
            self.btn_run.config(state="normal")
        except Exception as e:
            messagebox.showerror("错误", f"无法读取文件夹: {str(e)}")

    def clean_text(self, text):
        if not text: return ""
        safe_name = text.lower()
        safe_name = safe_name.replace(" ", "_")
        for char in ["/", "\\", ":", "*", "?", "\"", "<", ">", "|", "'", "’"]:
            safe_name = safe_name.replace(char, "")
        while "__" in safe_name:
            safe_name = safe_name.replace("__", "_")
        return safe_name.strip("_")

    def call_silicon_ai(self, text, target_lang_desc, api_key, model_id):
        url = "https://api.siliconflow.cn/v1/chat/completions"
        prompt = f"Translate the following filename into {target_lang_desc}. Output ONLY the translated text, no explanation. Source: {text}"
        payload = {
            "model": model_id, # 使用用户选择的模型
            "messages": [{"role": "system", "content": "You are a translator."}, {"role": "user", "content": prompt}],
            "temperature": 0.3
        }
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content'].strip()
        except Exception as e:
            raise Exception(f"AI API Error: {str(e)}")

    # --- 翻译逻辑 ---

    def stop_translation(self):
        self.stop_event.set()
        self.status_label.config(text="正在停止...")
        self.btn_stop.config(state="disabled")

    def start_translation_thread(self):
        if not self.target_folder:
            messagebox.showwarning("提示", "请先选择文件夹！")
            return
        
        selected_items = self.tree.selection()
        items_to_process = selected_items if selected_items else self.tree.get_children()
        
        service = self.service_var.get()
        if service == "silicon":
            key = self.api_key_var.get().strip()
            if not key:
                messagebox.showwarning("提示", "使用硅基流动AI必须填写 API Key！")
                return
            # 保存Key和模型选择
            self.save_config()

        self.btn_preview.config(state="disabled", text="⏳ 处理中...")
        self.btn_stop.config(state="normal") 
        self.status_label.config(text="正在连接翻译服务...")
        
        self.stop_event.clear()
        self.progress['maximum'] = len(items_to_process)
        self.progress['value'] = 0
        
        thread = threading.Thread(target=self.perform_translation, args=(items_to_process,))
        thread.daemon = True
        thread.start()

    def perform_translation(self, items):
        rule_selection = self.rule_var.get()
        service = self.service_var.get()
        api_key = self.api_key_var.get().strip()
        model_id = self.model_var.get().strip() # 获取选中的模型
        
        translator_en = None
        translator_zh = None
        
        if service == "google":
            translator_en = GoogleTranslator(source='auto', target='en')
            translator_zh = GoogleTranslator(source='auto', target='zh-CN')
        
        updated_items = []
        total = len(items)
        
        for index, item_id in enumerate(items):
            if self.stop_event.is_set():
                self.root.after(0, lambda: self.status_label.config(text="操作已停止"))
                break

            original_full_name = self.tree.item(item_id)['values'][1]
            name, ext = os.path.splitext(original_full_name)
            
            try:
                def get_trans(target_code, target_desc):
                    if service == "silicon":
                        # 传入模型ID
                        return self.call_silicon_ai(name, target_desc, api_key, model_id)
                    elif service == "google":
                        return translator_en.translate(name) if target_code == "en" else translator_zh.translate(name)

                final_name_base = ""
                
                # 规则处理
                if "纯英文" in rule_selection:
                    raw = get_trans("en", "English")
                    final_name_base = self.clean_text(raw)
                elif "纯中文" in rule_selection:
                    raw = get_trans("zh", "Simplified Chinese")
                    final_name_base = self.clean_text(raw)
                elif "英文_中文" in rule_selection:
                    raw_en = get_trans("en", "English")
                    raw_zh = get_trans("zh", "Simplified Chinese")
                    final_name_base = f"{self.clean_text(raw_en)}_{self.clean_text(raw_zh)}"
                elif "中文_英文" in rule_selection:
                    raw_zh = get_trans("zh", "Simplified Chinese")
                    raw_en = get_trans("en", "English")
                    final_name_base = f"{self.clean_text(raw_zh)}_{self.clean_text(raw_en)}"
                
                new_full_name = f"{final_name_base}{ext}"
                updated_items.append((item_id, new_full_name, "预览中", None))
                
                self.root.after(0, lambda idx=index: self.update_progress(idx + 1, total, name))
                
            except Exception as e:
                print(f"Error: {e}")
                updated_items.append((item_id, f"[失败] {original_full_name}", "出错", "error"))
                self.root.after(0, lambda idx=index: self.update_progress(idx + 1, total, "出错"))

        self.root.after(0, lambda: self.finish_translation(updated_items))

    def update_progress(self, current, total, filename):
        self.progress['value'] = current
        self.status_label.config(text=f"正在处理 ({current}/{total}): {filename}")

    def finish_translation(self, updated_items):
        for item_id, new_name, status, tag_override in updated_items:
            old_vals = self.tree.item(item_id)
            old_tags = old_vals['tags']
            final_tags = (tag_override,) if tag_override else (old_tags[0] if old_tags else 'odd',)
            self.tree.item(item_id, values=(status, old_vals['values'][1], new_name), tags=final_tags)
            
        self.btn_preview.config(state="normal", text="⚡ 生成翻译预览")
        self.btn_stop.config(state="disabled")
        
        if not self.stop_event.is_set():
            self.status_label.config(text="操作完成！请检查预览结果。")
        else:
            self.status_label.config(text="用户已停止操作。")

    # --- 交互逻辑 ---

    def show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            if len(self.tree.selection()) <= 1:
                self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def on_double_click(self, event):
        self.manual_edit_selected()

    def manual_edit_selected(self):
        selected = self.tree.selection()
        if not selected: return
        item_id = selected[0]
        values = self.tree.item(item_id)['values']
        current = values[2].replace("[失败] ", "")
        
        new_name = simpledialog.askstring("手动修改", "编辑新文件名:", initialvalue=current, parent=self.root)
        if new_name:
            self.tree.item(item_id, values=("手动", values[1], new_name))

    def retry_selected_translation(self):
        self.start_translation_thread()

    def reset_selected(self):
        for item_id in self.tree.selection():
            original = self.tree.item(item_id)['values'][1]
            self.tree.item(item_id, values=("重置", original, original))

    # --- 批量工具函数 ---
    
    def _apply_tool(self, callback):
        items = self.tree.get_children()
        count = 0
        for item_id in items:
            values = self.tree.item(item_id)['values']
            current = values[2]
            if current.startswith("[失败]"): continue
            
            new_val = callback(current, item_id, count)
            if new_val:
                self.tree.item(item_id, values=("已修饰", values[1], new_val))
                count += 1
        self.status_label.config(text=f"批量工具应用完成，影响 {count} 个文件")

    def tool_replace(self):
        find_s = self.ent_find.get(); rep_s = self.ent_rep.get()
        if not find_s: return
        self._apply_tool(lambda t, i, c: t.replace(find_s, rep_s))

    def tool_add_fix(self):
        pre = self.ent_prefix.get(); suf = self.ent_suffix.get()
        def add_fix(t, i, c):
            n, e = os.path.splitext(t)
            return f"{pre}{n}{suf}{e}"
        self._apply_tool(add_fix)

    def tool_sequence(self):
        base = self.ent_seq_name.get()
        try: start = int(self.ent_seq_start.get())
        except: start = 1
        def apply_seq(t, i, c):
            _, e = os.path.splitext(t)
            return f"{base}_{str(start + c).zfill(3)}{e}"
        self._apply_tool(apply_seq)

    def tool_extension(self):
        ext = self.ent_ext.get().strip()
        if not ext: return
        if not ext.startswith("."): ext = "." + ext
        self._apply_tool(lambda t, i, c: os.path.splitext(t)[0] + ext)

    def apply_rename(self):
        if not messagebox.askyesno("确认", "确定要将这些文件重命名吗？此操作不可撤销。"): return
        
        success, fail = 0, 0
        for item in self.tree.get_children():
            values = self.tree.item(item)['values']
            old_n, new_n = values[1], values[2]
            
            if "[失败]" in new_n or not new_n or old_n == new_n: continue
            
            try:
                os.rename(os.path.join(self.target_folder, old_n), os.path.join(self.target_folder, new_n))
                self.tree.item(item, values=("✅ 完成", old_n, new_n))
                success += 1
            except Exception as e:
                self.tree.item(item, values=("❌ 出错", old_n, str(e)), tags=('error',))
                fail += 1
                
        messagebox.showinfo("完成", f"重命名结束！\n成功: {success}\n失败: {fail}")
        self.btn_run.config(state="disabled")

if __name__ == "__main__":
    root = tk.Tk()
    app = FileRenamerApp(root)
    root.mainloop()