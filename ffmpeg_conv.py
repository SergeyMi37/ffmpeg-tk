import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import subprocess
import threading
from pathlib import Path
import shlex
import re
import json
import sys

class VideoConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("Конвертер WebM/Ogg в MP4/MP3 и Обрезка видео")
        self.root.geometry("900x700")
        
        # Список файлов для конвертации
        self.file_list = []
        # Список файлов для обрезки
        self.crop_file_list = []
        
        # Путь к файлу настроек
        self.settings_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")
        
        # Создаем интерфейс
        self.create_widgets()
        
        # Загружаем настройки
        self.load_settings()
        
    def create_widgets(self):
        # Создаем меню
        self.create_menu()
        
        # Создаем вкладки
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Вкладка конвертации
        self.convert_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.convert_frame, text="Конвертация")
        self.create_convert_tab()
        
        # Вкладка обрезки видео
        self.crop_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.crop_frame, text="Обрезка видео")
        self.create_crop_tab()
        
        # Индикатор выполнения (общий для обеих вкладок)
        self.progress = ttk.Progressbar(self.root, mode='determinate')
        self.progress.pack(fill=tk.X, padx=10, pady=5)
        
        # Статус (общий для обеих вкладок)
        self.status_label = ttk.Label(self.root, text="Готово")
        self.status_label.pack(pady=5)
        
        # Индикатор выполнения
        self.is_converting = False
        
    def create_menu(self):
        """Создание меню программы"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Меню Файл
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Файл", menu=file_menu)
        file_menu.add_command(label="Сохранить настройки", command=self.save_settings)
        file_menu.add_command(label="Загрузить настройки", command=self.load_settings_dialog)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.root.quit)
        
        # Меню Настройки
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Настройки", menu=settings_menu)
        settings_menu.add_command(label="Сбросить настройки", command=self.reset_settings)
        settings_menu.add_command(label="О программе", command=self.show_about)
        
    def create_convert_tab(self):
        """Создание интерфейса для вкладки конвертации"""
        # Фрейм для выбора файлов
        file_frame = ttk.LabelFrame(self.convert_frame, text="Выбор файлов", padding=10)
        file_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Кнопки выбора файлов
        button_frame = ttk.Frame(file_frame)
        button_frame.pack(fill=tk.X)
        
        self.select_files_btn = ttk.Button(button_frame, text="Добавить файлы", command=self.select_files)
        self.select_files_btn.pack(side=tk.LEFT, padx=5)
        
        self.select_folder_btn = ttk.Button(button_frame, text="Добавить папку", command=self.select_folder)
        self.select_folder_btn.pack(side=tk.LEFT, padx=5)
        
        self.clear_btn = ttk.Button(button_frame, text="Очистить список", command=self.clear_files)
        self.clear_btn.pack(side=tk.LEFT, padx=5)
        
        # Список файлов
        list_frame = ttk.Frame(file_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.file_listbox = tk.Listbox(list_frame, selectmode=tk.EXTENDED)
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.file_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_listbox.config(yscrollcommand=scrollbar.set)
        
        # Фрейм для выбора формата
        format_frame = ttk.LabelFrame(self.convert_frame, text="Формат конвертации", padding=10)
        format_frame.pack(fill=tk.X, padx=10, pady=5)
        
        format_frame_inner = ttk.Frame(format_frame)
        format_frame_inner.pack()
        
        self.output_format = tk.StringVar(value="mp4")
        format_radio_frame = ttk.Frame(format_frame_inner)
        format_radio_frame.pack()
        
        ttk.Radiobutton(format_radio_frame, text="MP4", variable=self.output_format, value="mp4").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(format_radio_frame, text="MP3", variable=self.output_format, value="mp3").pack(side=tk.LEFT, padx=10)
        
        # Фрейм для настроек MP3
        self.mp3_settings_frame = ttk.LabelFrame(self.convert_frame, text="Настройки MP3", padding=10)
        self.mp3_settings_frame.pack(fill=tk.X, padx=10, pady=5)
        
        bitrate_frame = ttk.Frame(self.mp3_settings_frame)
        bitrate_frame.pack()
        
        ttk.Label(bitrate_frame, text="Битрейт:").pack(side=tk.LEFT)
        self.bitrate_var = tk.StringVar(value="192k")
        bitrate_combo = ttk.Combobox(bitrate_frame, textvariable=self.bitrate_var,
                                   values=["64k", "128k", "192k", "256k", "320k"], width=10)
        bitrate_combo.pack(side=tk.LEFT, padx=5)
        
        # Фрейм для кнопок управления
        control_frame = ttk.Frame(self.convert_frame)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.convert_btn = ttk.Button(control_frame, text="Начать конвертацию", command=self.start_conversion)
        self.convert_btn.pack(side=tk.RIGHT, padx=5)
        
        self.stop_btn = ttk.Button(control_frame, text="Остановить", command=self.stop_conversion, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.RIGHT, padx=5)
        
        # Привязка события изменения формата
        self.output_format.trace('w', self.on_format_change)
        
    def create_crop_tab(self):
        """Создание интерфейса для вкладки обрезки видео"""
        # Фрейм для выбора файлов
        crop_file_frame = ttk.LabelFrame(self.crop_frame, text="Выбор видео для обрезки", padding=10)
        crop_file_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Кнопки выбора файлов
        crop_button_frame = ttk.Frame(crop_file_frame)
        crop_button_frame.pack(fill=tk.X)
        
        self.select_crop_files_btn = ttk.Button(crop_button_frame, text="Добавить видео", command=self.select_crop_files)
        self.select_crop_files_btn.pack(side=tk.LEFT, padx=5)
        
        self.clear_crop_btn = ttk.Button(crop_button_frame, text="Очистить список", command=self.clear_crop_files)
        self.clear_crop_btn.pack(side=tk.LEFT, padx=5)
        
        self.preview_crop_btn = ttk.Button(crop_button_frame, text="Предпросмотр", command=self.preview_video)
        self.preview_crop_btn.pack(side=tk.LEFT, padx=5)
        
        # Список файлов для обрезки
        crop_list_frame = ttk.Frame(crop_file_frame)
        crop_list_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.crop_listbox = tk.Listbox(crop_list_frame, selectmode=tk.SINGLE, height=5)
        self.crop_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.crop_listbox.bind('<<ListboxSelect>>', self.on_crop_file_select)
        
        crop_scrollbar = ttk.Scrollbar(crop_list_frame, orient=tk.VERTICAL, command=self.crop_listbox.yview)
        crop_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.crop_listbox.config(yscrollcommand=crop_scrollbar.set)
        
        # Фрейм для настроек обрезки
        crop_settings_frame = ttk.LabelFrame(self.crop_frame, text="Настройки обрезки", padding=10)
        crop_settings_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Информация о видео
        self.video_info_label = ttk.Label(crop_settings_frame, text="Выберите видео для просмотра информации", wraplength=800)
        self.video_info_label.pack(pady=5)
        
        # Время начала
        start_frame = ttk.Frame(crop_settings_frame)
        start_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(start_frame, text="Время начала (ЧЧ:ММ:СС.МС или секунды):", width=30).pack(side=tk.LEFT)
        self.start_time_var = tk.StringVar(value="00:00:00")
        start_entry = ttk.Entry(start_frame, textvariable=self.start_time_var, width=20)
        start_entry.pack(side=tk.LEFT, padx=5)
        
        # Кнопки для быстрой установки времени
        ttk.Button(start_frame, text="+5 сек", command=lambda: self.add_time('start', 5)).pack(side=tk.LEFT, padx=2)
        ttk.Button(start_frame, text="+10 сек", command=lambda: self.add_time('start', 10)).pack(side=tk.LEFT, padx=2)
        
        # Время окончания
        end_frame = ttk.Frame(crop_settings_frame)
        end_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(end_frame, text="Время окончания (ЧЧ:ММ:СС.МС или секунды):", width=30).pack(side=tk.LEFT)
        self.end_time_var = tk.StringVar(value="00:01:00")
        end_entry = ttk.Entry(end_frame, textvariable=self.end_time_var, width=20)
        end_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(end_frame, text="+5 сек", command=lambda: self.add_time('end', 5)).pack(side=tk.LEFT, padx=2)
        ttk.Button(end_frame, text="+10 сек", command=lambda: self.add_time('end', 10)).pack(side=tk.LEFT, padx=2)
        
        # Продолжительность (альтернатива времени окончания)
        duration_frame = ttk.Frame(crop_settings_frame)
        duration_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(duration_frame, text="Или длительность (ЧЧ:ММ:СС.МС):", width=30).pack(side=tk.LEFT)
        self.duration_var = tk.StringVar(value="")
        duration_entry = ttk.Entry(duration_frame, textvariable=self.duration_var, width=20)
        duration_entry.pack(side=tk.LEFT, padx=5)
        ttk.Label(duration_frame, text="(если указана, время окончания игнорируется)").pack(side=tk.LEFT, padx=5)
        
        # Точность обрезки
        accuracy_frame = ttk.Frame(crop_settings_frame)
        accuracy_frame.pack(fill=tk.X, pady=5)
        
        self.accurate_crop_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(accuracy_frame, text="Точная обрезка (покадровая, медленнее)", 
                       variable=self.accurate_crop_var).pack(side=tk.LEFT)
        
        ttk.Label(accuracy_frame, text="(если отключено - быстрая обрезка по ключевым кадрам)").pack(side=tk.LEFT, padx=10)
        
        # Фрейм для кнопок управления
        crop_control_frame = ttk.Frame(self.crop_frame)
        crop_control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.start_crop_btn = ttk.Button(crop_control_frame, text="Начать обрезку", command=self.start_cropping)
        self.start_crop_btn.pack(side=tk.RIGHT, padx=5)
        
        self.stop_crop_btn = ttk.Button(crop_control_frame, text="Остановить", command=self.stop_conversion, state=tk.DISABLED)
        self.stop_crop_btn.pack(side=tk.RIGHT, padx=5)
        
    def on_format_change(self, *args):
        """Обработчик изменения формата конвертации"""
        if self.output_format.get() == "mp3":
            self.mp3_settings_frame.pack(fill=tk.X, padx=10, pady=5)
        else:
            self.mp3_settings_frame.pack_forget()
    
    def select_files(self):
        """Выбор файлов для конвертации"""
        files = filedialog.askopenfilenames(
            title="Выберите файлы для конвертации",
            filetypes=[
                ("WebM файлы", "*.webm"),
                ("Ogg файлы", "*.ogg"),
                ("Все поддерживаемые", "*.webm *.ogg"),
                ("Все файлы", "*.*")
            ]
        )
        
        for file in files:
            if file not in self.file_list:
                self.file_list.append(file)
                self.file_listbox.insert(tk.END, os.path.basename(file))
                
    def select_folder(self):
        """Выбор папки для конвертации"""
        folder = filedialog.askdirectory(title="Выберите папку с файлами")
        if folder:
            for file in os.listdir(folder):
                if file.lower().endswith(('.webm', '.ogg')):
                    file_path = os.path.join(folder, file)
                    if file_path not in self.file_list:
                        self.file_list.append(file_path)
                        self.file_listbox.insert(tk.END, file)
                        
    def clear_files(self):
        """Очистка списка файлов"""
        self.file_list.clear()
        self.file_listbox.delete(0, tk.END)
        
    def select_crop_files(self):
        """Выбор видео для обрезки"""
        files = filedialog.askopenfilenames(
            title="Выберите видео для обрезки",
            filetypes=[
                ("Видео файлы", "*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm"),
                ("Все файлы", "*.*")
            ]
        )
        
        for file in files:
            if file not in self.crop_file_list:
                self.crop_file_list.append(file)
                self.crop_listbox.insert(tk.END, os.path.basename(file))
    
    def clear_crop_files(self):
        """Очистка списка файлов для обрезки"""
        self.crop_file_list.clear()
        self.crop_listbox.delete(0, tk.END)
        self.video_info_label.config(text="Выберите видео для просмотра информации")
    
    def on_crop_file_select(self, event):
        """Обработчик выбора файла для обрезки"""
        selection = self.crop_listbox.curselection()
        if selection:
            index = selection[0]
            file_path = self.crop_file_list[index]
            self.get_video_info(file_path)
    
    def get_video_info(self, file_path):
        """Получение информации о видео"""
        try:
            cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', file_path]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Простой парсинг для получения длительности
            import json
            data = json.loads(result.stdout)
            
            duration = float(data['format'].get('duration', 0))
            
            # Форматирование длительности
            hours = int(duration // 3600)
            minutes = int((duration % 3600) // 60)
            seconds = duration % 60
            
            if hours > 0:
                duration_str = f"{hours:02d}:{minutes:02d}:{seconds:06.3f}"
            else:
                duration_str = f"{minutes:02d}:{seconds:06.3f}"
            
            # Получаем информацию о видео и аудио
            video_codec = "N/A"
            audio_codec = "N/A"
            
            for stream in data['streams']:
                if stream['codec_type'] == 'video':
                    video_codec = stream.get('codec_name', 'N/A')
                elif stream['codec_type'] == 'audio':
                    audio_codec = stream.get('codec_name', 'N/A')
            
            self.video_info_label.config(
                text=f"Файл: {os.path.basename(file_path)}\n"
                     f"Длительность: {duration_str}\n"
                     f"Видео кодек: {video_codec}, Аудио кодек: {audio_codec}"
            )
            
            # Устанавливаем время окончания как длительность видео
            self.end_time_var.set(duration_str.split('.')[0])  # Без миллисекунд
            
        except Exception as e:
            self.video_info_label.config(text=f"Ошибка получения информации: {str(e)}")
    
    def preview_video(self):
        """Открыть видео в системном проигрывателе"""
        selection = self.crop_listbox.curselection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите видео для предпросмотра")
            return
        
        index = selection[0]
        file_path = self.crop_file_list[index]
        
        try:
            if os.name == 'nt':  # Windows
                os.startfile(file_path)
            elif os.name == 'posix':  # macOS и Linux
                subprocess.run(['open' if sys.platform == 'darwin' else 'xdg-open', file_path])
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть видео: {str(e)}")
    
    def add_time(self, time_type, seconds):
        """Добавить секунды к времени"""
        if time_type == 'start':
            current = self.start_time_var.get()
            var = self.start_time_var
        else:
            current = self.end_time_var.get()
            var = self.end_time_var
        
        try:
            # Парсим время
            total_seconds = self.parse_time_to_seconds(current)
            total_seconds += seconds
            
            # Форматируем обратно
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            secs = total_seconds % 60
            
            if hours > 0:
                new_time = f"{hours:02d}:{minutes:02d}:{secs:02d}"
            else:
                new_time = f"{minutes:02d}:{secs:02d}"
            
            var.set(new_time)
            
        except ValueError:
            # Если не удалось распарсить, игнорируем
            pass
    
    def parse_time_to_seconds(self, time_str):
        """Преобразование времени в секунды"""
        time_str = time_str.strip()
        
        # Проверяем, не число ли это
        try:
            return float(time_str)
        except ValueError:
            pass
        
        # Парсим формат ЧЧ:ММ:СС.МС или ММ:СС.МС
        parts = time_str.split(':')
        
        if len(parts) == 3:
            hours = float(parts[0])
            minutes = float(parts[1])
            seconds = float(parts[2])
            return hours * 3600 + minutes * 60 + seconds
        elif len(parts) == 2:
            minutes = float(parts[0])
            seconds = float(parts[1])
            return minutes * 60 + seconds
        else:
            raise ValueError(f"Неверный формат времени: {time_str}")
    
    def validate_crop_settings(self):
        """Проверка настроек обрезки"""
        try:
            start = self.parse_time_to_seconds(self.start_time_var.get())
            
            if self.duration_var.get().strip():
                duration = self.parse_time_to_seconds(self.duration_var.get())
                end = start + duration
            else:
                end = self.parse_time_to_seconds(self.end_time_var.get())
            
            if start < 0 or end < 0:
                messagebox.showerror("Ошибка", "Время не может быть отрицательным")
                return None
            
            if end <= start:
                messagebox.showerror("Ошибка", "Время окончания должно быть больше времени начала")
                return None
            
            return start, end
            
        except ValueError as e:
            messagebox.showerror("Ошибка", f"Неверный формат времени: {str(e)}")
            return None
    
    def start_cropping(self):
        """Начало обрезки видео"""
        if not self.crop_file_list:
            messagebox.showwarning("Предупреждение", "Не выбрано ни одного видео для обрезки")
            return
        
        if not self.validate_ffmpeg():
            messagebox.showerror("Ошибка", "FFmpeg не найден. Пожалуйста, установите FFmpeg и добавьте его в PATH")
            return
        
        # Проверяем настройки обрезки для первого файла (для предупреждения)
        selection = self.crop_listbox.curselection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите видео для обрезки в списке")
            return
        
        settings = self.validate_crop_settings()
        if not settings:
            return
        
        self.is_converting = True
        self.start_crop_btn.config(state=tk.DISABLED)
        self.stop_crop_btn.config(state=tk.NORMAL)
        self.status_label.config(text="Идет обрезка видео...")
        
        # Запуск обрезки в отдельном потоке
        thread = threading.Thread(target=self.crop_files_thread)
        thread.daemon = True
        thread.start()
    
    def crop_files_thread(self):
        """Обрезка видео в отдельном потоке"""
        total_files = len(self.crop_file_list)
        cropped_count = 0
        
        for i, input_file in enumerate(self.crop_file_list):
            if not self.is_converting:
                break
            
            try:
                # Получаем настройки обрезки
                start = self.parse_time_to_seconds(self.start_time_var.get())
                
                if self.duration_var.get().strip():
                    duration = self.parse_time_to_seconds(self.duration_var.get())
                    end = None
                else:
                    duration = None
                    end = self.parse_time_to_seconds(self.end_time_var.get())
                
                # Определяем имя выходного файла
                input_path = Path(input_file)
                output_file = input_path.parent / f"{input_path.stem}_cropped{input_path.suffix}"
                
                # Если файл уже существует, добавляем суффикс
                counter = 1
                while output_file.exists():
                    output_file = input_path.parent / f"{input_path.stem}_cropped_{counter}{input_path.suffix}"
                    counter += 1
                
                # Выполняем обрезку
                success = self.crop_video(input_file, str(output_file), start, end, duration)
                
                if success:
                    cropped_count += 1
                    self.root.after(0, lambda i=i: self.update_progress(i + 1, total_files))
                else:
                    self.root.after(0, lambda: self.status_label.config(
                        text=f"Ошибка обрезки: {os.path.basename(input_file)}"))
                
            except Exception as e:
                self.root.after(0, lambda: self.status_label.config(text=f"Ошибка: {str(e)}"))
        
        self.root.after(0, lambda: self.cropping_finished(cropped_count, total_files))
    
    def crop_video(self, input_file, output_file, start, end=None, duration=None):
        """Обрезка видео с помощью FFmpeg"""
        try:
            # Форматируем время для FFmpeg
            start_str = self.format_time_for_ffmpeg(start)
            
            # Строим команду
            if self.accurate_crop_var.get():
                # Точная обрезка (перекодирование)
                if duration:
                    cmd = ['ffmpeg', '-i', input_file, '-ss', start_str, '-t', 
                           self.format_time_for_ffmpeg(duration), '-c:v', 'libx264', 
                           '-c:a', 'aac', output_file]
                else:
                    cmd = ['ffmpeg', '-i', input_file, '-ss', start_str, '-to', 
                           self.format_time_for_ffmpeg(end), '-c:v', 'libx264', 
                           '-c:a', 'aac', output_file]
            else:
                # Быстрая обрезка (копирование)
                if duration:
                    cmd = ['ffmpeg', '-ss', start_str, '-i', input_file, '-t', 
                           self.format_time_for_ffmpeg(duration), '-c', 'copy', output_file]
                else:
                    cmd = ['ffmpeg', '-ss', start_str, '-i', input_file, '-to', 
                           self.format_time_for_ffmpeg(end), '-c', 'copy', output_file]
            
            # Запускаем процесс
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            return True
            
        except subprocess.CalledProcessError:
            return False
    
    def format_time_for_ffmpeg(self, seconds):
        """Форматирование времени для FFmpeg"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"
        else:
            return f"{minutes:02d}:{secs:06.3f}"
    
    def cropping_finished(self, cropped_count, total_files):
        """Завершение обрезки"""
        self.is_converting = False
        self.start_crop_btn.config(state=tk.NORMAL)
        self.stop_crop_btn.config(state=tk.DISABLED)
        self.progress['value'] = 0
        
        if cropped_count == total_files:
            self.status_label.config(text=f"Обрезка завершена! Обработано: {cropped_count}/{total_files}")
        else:
            self.status_label.config(text=f"Обрезка завершена с ошибками. Обработано: {cropped_count}/{total_files}")
    
    def validate_ffmpeg(self):
        """Проверка наличия FFmpeg"""
        try:
            subprocess.run(['ffmpeg', '-version'], 
                         stdout=subprocess.DEVNULL, 
                         stderr=subprocess.DEVNULL, 
                         check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def convert_file(self, input_file, output_file):
        """Конвертация одного файла"""
        try:
            if self.output_format.get() == "mp4":
                # Конвертация WebM в MP4
                cmd = ['ffmpeg', '-i', input_file, '-c:v', 'libx264', '-c:a', 'aac', output_file]
            else:
                # Конвертация в MP3 с выбором битрейта
                bitrate = self.bitrate_var.get()
                cmd = ['ffmpeg', '-i', input_file, '-vn', '-ar', '44100', '-ac', '2', '-ab', bitrate, '-f', 'mp3', output_file]
                
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            return True
        except subprocess.CalledProcessError:
            return False
    
    def start_conversion(self):
        """Начало конвертации"""
        if not self.file_list:
            messagebox.showwarning("Предупреждение", "Не выбрано ни одного файла для конвертации")
            return
            
        if not self.validate_ffmpeg():
            messagebox.showerror("Ошибка", "FFmpeg не найден. Пожалуйста, установите FFmpeg и добавьте его в PATH")
            return
            
        self.is_converting = True
        self.convert_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_label.config(text="Идет конвертация...")
        
        # Запуск конвертации в отдельном потоке
        thread = threading.Thread(target=self.convert_files_thread)
        thread.daemon = True
        thread.start()
    
    def convert_files_thread(self):
        """Конвертация файлов в отдельном потоке"""
        total_files = len(self.file_list)
        converted_count = 0
        
        for i, input_file in enumerate(self.file_list):
            if not self.is_converting:
                break
                
            try:
                # Определяем имя выходного файла
                input_path = Path(input_file)
                if self.output_format.get() == "mp4":
                    output_file = input_path.parent / f"{input_path.stem}.mp4"
                else:
                    output_file = input_path.parent / f"{input_path.stem}.mp3"
                    
                # Если файл уже существует, добавляем суффикс
                counter = 1
                while output_file.exists():
                    if self.output_format.get() == "mp4":
                        output_file = input_path.parent / f"{input_path.stem}_{counter}.mp4"
                    else:
                        output_file = input_path.parent / f"{input_path.stem}_{counter}.mp3"
                    counter += 1
                    
                # Выполняем конвертацию
                success = self.convert_file(input_file, str(output_file))
                
                if success:
                    converted_count += 1
                    self.root.after(0, lambda i=i: self.update_progress(i + 1, total_files))
                else:
                    self.root.after(0, lambda: self.status_label.config(text=f"Ошибка конвертации: {os.path.basename(input_file)}"))
                    
            except Exception as e:
                self.root.after(0, lambda: self.status_label.config(text=f"Ошибка: {str(e)}"))
                
        self.root.after(0, lambda: self.conversion_finished(converted_count, total_files))
    
    def update_progress(self, current, total):
        """Обновление прогресса"""
        percentage = (current / total) * 100
        self.progress['value'] = percentage
        self.status_label.config(text=f"Обработка: {current}/{total}")
    
    def conversion_finished(self, converted_count, total_files):
        """Завершение конвертации"""
        self.is_converting = False
        self.convert_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.progress['value'] = 0
        
        if converted_count == total_files:
            self.status_label.config(text=f"Конвертация завершена! Обработано: {converted_count}/{total_files}")
        else:
            self.status_label.config(text=f"Конвертация завершена с ошибками. Обработано: {converted_count}/{total_files}")
    
    def stop_conversion(self):
        """Остановка конвертации/обрезки"""
        self.is_converting = False
        self.convert_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.start_crop_btn.config(state=tk.NORMAL)
        self.stop_crop_btn.config(state=tk.DISABLED)
        self.status_label.config(text="Обработка остановлена")
    
    # Методы для работы с настройками
    def save_settings(self):
        """Сохранение настроек в JSON файл"""
        try:
            settings = {
                'convert_tab': {
                    'output_format': self.output_format.get(),
                    'bitrate': self.bitrate_var.get(),
                    'file_list': self.file_list
                },
                'crop_tab': {
                    'start_time': self.start_time_var.get(),
                    'end_time': self.end_time_var.get(),
                    'duration': self.duration_var.get(),
                    'accurate_crop': self.accurate_crop_var.get(),
                    'crop_file_list': self.crop_file_list
                },
                'window': {
                    'geometry': self.root.geometry(),
                    'active_tab': self.notebook.index(self.notebook.select())
                }
            }
            
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=4)
            
            messagebox.showinfo("Успех", f"Настройки сохранены в файл:\n{self.settings_file}")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить настройки: {str(e)}")
    
    def load_settings(self):
        """Загрузка настроек из JSON файла при старте"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                
                # Загрузка настроек вкладки конвертации
                if 'convert_tab' in settings:
                    convert_settings = settings['convert_tab']
                    
                    if 'output_format' in convert_settings:
                        self.output_format.set(convert_settings['output_format'])
                    
                    if 'bitrate' in convert_settings:
                        self.bitrate_var.set(convert_settings['bitrate'])
                    
                    if 'file_list' in convert_settings and isinstance(convert_settings['file_list'], list):
                        for file_path in convert_settings['file_list']:
                            if os.path.exists(file_path) and file_path not in self.file_list:
                                self.file_list.append(file_path)
                                self.file_listbox.insert(tk.END, os.path.basename(file_path))
                
                # Загрузка настроек вкладки обрезки
                if 'crop_tab' in settings:
                    crop_settings = settings['crop_tab']
                    
                    if 'start_time' in crop_settings:
                        self.start_time_var.set(crop_settings['start_time'])
                    
                    if 'end_time' in crop_settings:
                        self.end_time_var.set(crop_settings['end_time'])
                    
                    if 'duration' in crop_settings:
                        self.duration_var.set(crop_settings['duration'])
                    
                    if 'accurate_crop' in crop_settings:
                        self.accurate_crop_var.set(crop_settings['accurate_crop'])
                    
                    if 'crop_file_list' in crop_settings and isinstance(crop_settings['crop_file_list'], list):
                        for file_path in crop_settings['crop_file_list']:
                            if os.path.exists(file_path) and file_path not in self.crop_file_list:
                                self.crop_file_list.append(file_path)
                                self.crop_listbox.insert(tk.END, os.path.basename(file_path))
                
                # Загрузка настроек окна
                if 'window' in settings:
                    window_settings = settings['window']
                    
                    if 'geometry' in window_settings:
                        self.root.geometry(window_settings['geometry'])
                    
                    if 'active_tab' in window_settings:
                        self.notebook.select(window_settings['active_tab'])
                
                self.status_label.config(text="Настройки загружены")
                
        except Exception as e:
            print(f"Ошибка загрузки настроек: {str(e)}")
    
    def load_settings_dialog(self):
        """Загрузка настроек через диалог"""
        try:
            if os.path.exists(self.settings_file):
                result = messagebox.askyesno(
                    "Загрузка настроек",
                    f"Загрузить настройки из файла?\n{self.settings_file}"
                )
                if result:
                    self.load_settings()
                    messagebox.showinfo("Успех", "Настройки успешно загружены")
            else:
                messagebox.showwarning("Предупреждение", "Файл настроек не найден")
                
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить настройки: {str(e)}")
    
    def reset_settings(self):
        """Сброс настроек к значениям по умолчанию"""
        result = messagebox.askyesno(
            "Сброс настроек",
            "Вы уверены, что хотите сбросить все настройки к значениям по умолчанию?"
        )
        
        if result:
            # Сброс настроек конвертации
            self.output_format.set("mp4")
            self.bitrate_var.set("192k")
            self.clear_files()
            
            # Сброс настроек обрезки
            self.start_time_var.set("00:00:00")
            self.end_time_var.set("00:01:00")
            self.duration_var.set("")
            self.accurate_crop_var.set(False)
            self.clear_crop_files()
            
            # Сброс геометрии окна
            self.root.geometry("900x700")
            
            self.status_label.config(text="Настройки сброшены к значениям по умолчанию")
    
    def show_about(self):
        """Отображение информации о программе"""
        about_text = """
Конвертер видео и обрезка видео
        
Версия: 2.0
Разработчик: Python FFmpeg GUI
        
Возможности:
• Конвертация WebM/Ogg в MP4/MP3
• Обрезка видео с выбором времени
• Быстрая и точная обрезка
• Сохранение и загрузка настроек
        
Требования:
• FFmpeg должен быть установлен в системе
        """
        
        messagebox.showinfo("О программе", about_text)

def main():
    root = tk.Tk()
    app = VideoConverter(root)
    root.mainloop()

if __name__ == "__main__":
    main()