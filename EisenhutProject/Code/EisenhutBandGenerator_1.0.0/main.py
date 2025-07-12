from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.properties import StringProperty, NumericProperty, ObjectProperty, ListProperty
from kivy.uix.spinner import Spinner
from kivy.clock import Clock
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from kivy.core.window import Window
from kivy.uix.button import Button
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.metrics import dp
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import os
import json

ABILITIES = {
    'Движение':
        '''
            1. До конца хода, все персонажи кроме лидера, в радиусе 10 дюймов от него получают +2 дюйма к дистанции передвижения;
            2. Передвинуть, не находящегося в бою персонажа, на 5 дюймов в любом направлении;
            3. Персонаж автоматически выходит из ближнего боя и его можно передвинуть на 3 дюйма в любом направлении.''',
    'Защита':
        '''
            1. До своей следующей активации, все щитники, кроме лидера, в радиусе 10 дюймов от него получают бонусный куб защиты к6.
            2. Боец повышает куб защиты доспехов или щита на уровень вверх до своей следующей активации.
            3. Боец автоматически избавляется от кровотечения.
            4. До конца хода, все персонажи кроме лидера, в радиусе 10 дюймов от него получают способность Плечом к плечу.''',
    'Ближний бой':
        '''
            1. До конца хода, все персонажи кроме лидера, в радиусе 10 дюймов от него получает к6 - бонусный куб атаки в ближнем бою;
            2. Персонаж совершает атаку по возможности по всем противникам находящимся с ним в базовом контакте;
            3. Один раз за активацию, при нанесении раны сбивает противник с ног;
            4. До конца хода, все персонажи кроме лидера, в радиусе 10 дюймов от него получают способность Кровожадный.''',
    'Стрельба':
        '''
            1. До конца хода, все персонажи кроме лидера, в радиусе 10 дюймов от него получает к6 - бонусный куб атаки в дальнем бою;
            2. Один раз за активацию, боец может проигнорировать укрытие цели;
            3. Один раз за активацию, боец может перебросить один куб в тесте стрельбы;
            4. До конца хода, все персонажи кроме лидера, в радиусе 10 дюймов от него получают для дальнобойных атак способность Страшный.'''
}

CHARACTER_TYPE = {
    'Элитный боец': {'КП': 'к10', 'ОД': 3, 'abilities_count': 3, 'point_cost': 95},
    'Ветеран': {'КП': 'к8', 'ОД': 3, 'abilities_count': 2, 'point_cost': 75},
    'Новобранец': {'КП': 'к6', 'ОД': 3, 'abilities_count': 1, 'point_cost': 55},
    'Собака': {'КП': 'к6', 'ОД': 4, 'abilities_count': 1, 'default_ability': 'Животное', 'point_cost': 40}
}

class MainScreen(Screen):
    band_name_input = ObjectProperty(None)
    points_input = ObjectProperty(None)
    squad_label = ObjectProperty(None)
    points_label = ObjectProperty(None)

    def open_generator(self):
        # Получаем текст из TextInput
        band_name = self.band_name_input.text.strip()
        band_name = band_name.title()
        points_text = self.points_input.text.strip()

        # Проверка длины названия
        if not band_name:
            self.squad_label.text = 'Вы не ввели название!'
            return

        if not points_text:
            self.points_label.text = 'Вы не определили количество очков!'
            return

        if len(band_name) >= 31:
            self.squad_label.text = 'Вы превысили количество символов в названии! (макс. 30)'
            return

        if int(points_text) > 15000:
            self.points_label.text = 'Это значение ограничено 15000!'
            return

        if int(points_text) < 100:
            self.points_label.text = 'Это значение не может быть меньше 100!'
            return


        # Передаем данные в экран способностей
        abilities_screen = self.manager.get_screen('abilities')
        abilities_screen.band_name = band_name
        abilities_screen.points = points_text
        self.manager.current = 'abilities'


class AbilitySelectionScreen(Screen):
    ability1_spinner = ObjectProperty(None)
    ability2_spinner = ObjectProperty(None)
    description_label = ObjectProperty(None)
    available_abilities = ListProperty([])
    selected_abilities = ListProperty([])
    band_name = StringProperty('')
    points = StringProperty('')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.available_abilities = list(ABILITIES.keys())
        Clock.schedule_once(self._finish_init)

    def _finish_init(self, dt):
        self.update_spinners()
        self.description_label.text = "Описание появится здесь после выбора"

    def on_spinner_select(self, spinner, text):
        if text != "Выберите способность":
            spinner.background_color = (0.9, 0.9, 1, 1)
        if text == "Выберите способность":
            self.description_label.text = "Описание появится здесь после выбора"
            return

        self.update_available_abilities()
        self.update_description(text)
        self.update_selected_abilities()
        self.update_continue_button()

    def update_description(self, ability_name):
        if ability_name in ABILITIES:
            self.description_label.text = ABILITIES[ability_name]
            # Принудительное обновление текста
            self.description_label.texture_update()
            self.description_label.canvas.ask_update()

    def update_available_abilities(self):
        selected = [self.ability1_spinner.text, self.ability2_spinner.text]
        self.available_abilities = [
            a for a in ABILITIES.keys()
            if a not in selected and a != "Выберите способность"
        ]
        self.update_spinners()

    def update_spinners(self):
        values = ["Выберите способность"] + self.available_abilities
        self.ability1_spinner.values = values
        self.ability2_spinner.values = values

    def update_selected_abilities(self):
        self.selected_abilities = [
            a for a in [self.ability1_spinner.text, self.ability2_spinner.text]
            if a != "Выберите способность"
        ]

    def update_continue_button(self):
        self.ids.btn_continue.disabled = not self.can_proceed()

    def can_proceed(self):
        return len(self.selected_abilities) == 2

    def proceed_to_generator(self):
        if self.can_proceed():
            generator = self.manager.get_screen('generator')
            generator.set_data(self.band_name, self.points)
            generator.update_abilities(self.selected_abilities)
            self.manager.current = 'generator'

    def proceed_to_mainscreen(self):
        self.manager.current = 'main'


class GeneratorScreen(Screen):
    band_name = StringProperty('')
    points = StringProperty('')
    selected_fighter_index = NumericProperty(-1)  # Используем -1 вместо None
    static_label = ObjectProperty(None)
    abilities_label = ObjectProperty(None)
    fighters_layout = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.fighters = []
        self.abilities = []
        self.selected_fighter_index = -1

    def set_data(self, band_name, points):
        self.band_name = band_name
        self.points = points
        self.update_display()

    def update_abilities(self, abilities):
        self.abilities = abilities
        self.update_display()

    def update_display(self):
        #Обновляем все части интерфейса
        if not hasattr(self, 'static_label'):
            return

        fighters_cost = sum(f.get('total_cost', 0) for f in self.fighters)
        self.static_label.text = f"[size=24][b]{self.band_name}[/b][/size]\n\nОчки: {self.points}\nПотрачено: {fighters_cost}"

        abilities_text = "[b]Способности отряда:[/b]\n\n"
        for ability in self.abilities:
            abilities_text += f"[b]{ability}[/b]\n{ABILITIES.get(ability, '')}\n\n"

        if hasattr(self, 'abilities_label'):
            self.abilities_label.text = abilities_text

        self.update_fighters_list()

    def update_fighters_list(self):
        #Обновление списка бойцов
        if not hasattr(self, 'fighters_layout'):
            return

        self.fighters_layout.clear_widgets()

        for i, fighter in enumerate(self.fighters):
            card = BoxLayout(
                orientation='vertical',
                size_hint_y=None,
                spacing=dp(5),
                padding=dp(10),
            )

            # Заголовок с именем и стоимостью
            header = BoxLayout(size_hint_y=None, height=dp(50)) #регулирует отступ карточки бойца сверху
            header.add_widget(Label(
                text=f"[b]{fighter['name']}[/b]",
                size_hint_x=0.7,
                font_size='16sp',
                markup=True,
                color=(0, 0, 0, 1)
            ))
            header.add_widget(Label(
                text=f"{fighter['total_cost']} очков",
                size_hint_x=0.3,
                font_size='16sp',
                halign='right',
                color=(0, 0, 0, 1)
            ))
            card.add_widget(header)

            # Тип и характеристики
            card.add_widget(Label(
                text=f"{fighter['type']}\nКП: {fighter['stats']['КП']}, ОД: {fighter['stats']['ОД']}",
                size_hint_y=None,
                height=dp(40),
                font_size='14sp',
                color=(0, 0, 0, 1)
            ))

            # Способности
            if fighter['abilities']:
                abilities = Label(
                    text="Способности:\n" + "\n".join([f"• {ab['Название']}" for ab in fighter['abilities']]),
                    size_hint_y=None,
                    height=dp(20 + len(fighter['abilities']) * dp(18)),
                    font_size='14sp',
                    halign='left',
                    color=(0, 0, 0, 1)
                )
                card.add_widget(abilities)

            # Предметы
            if fighter['equipment']:
                items = Label(
                    text="Предметы:\n" + "\n".join(
                        [f"• {eq['Название']} ({eq['Цена']} очков)" for eq in fighter['equipment']]),
                    size_hint_y=None,
                    height=dp(20 + len(fighter['equipment']) * dp(18)),
                    font_size='14sp',
                    halign='left',
                    color=(0, 0, 0, 1)
                )
                card.add_widget(items)

            # Кнопки управления
            buttons = BoxLayout(
                size_hint_y=None,
                height=dp(40),
                spacing=dp(10)
            )
            edit_btn = Button(
                text='Редактировать',
                size_hint_x=0.4,
                background_color=(0.9, 0.9, 0.9, 1),
                on_press=lambda btn, idx=i: self.edit_fighter(idx)
            )
            delete_btn = Button(
                text='Удалить',
                size_hint_x=0.4,
                background_color=(0.9, 0.9, 0.9, 1),
                on_press=lambda btn, idx=i: self.delete_fighter(idx)
            )
            buttons.add_widget(edit_btn)
            buttons.add_widget(delete_btn)
            card.add_widget(buttons)

            card.height = sum(c.height for c in card.children)
            self.fighters_layout.add_widget(card)

    def show_add_fighter_popup(self):
        #Показ попапа добавления бойца
        try:
            available_points = int(self.points)
            if available_points <= 0:
                self.show_error("Недостаточно очков!")
                return

            popup = AddFighterPopup(self.add_fighter)
            popup.open()
        except Exception as e:
            self.show_error(f"Ошибка: {str(e)}")

    def add_fighter(self, fighter_data):
        #Добавление/обновление бойца
        if self.selected_fighter_index >= 0:  # Проверяем на -1
            self.fighters[self.selected_fighter_index] = fighter_data
            self.selected_fighter_index = -1  # Сбрасываем в -1
        else:
            self.fighters.append(fighter_data)

        self.points = str(int(self.points) - fighter_data['total_cost'])
        self.update_display()

    def edit_fighter(self, index):
        #Редактирование бойца
        if 0 <= index < len(self.fighters):
            self.selected_fighter_index = index  # Устанавливаем индекс
            fighter = self.fighters[index]
            self.points = str(int(self.points) + fighter['total_cost'])

            popup = AddFighterPopup(
                self.add_fighter,
                edit_mode=True,
                fighter_data=fighter
            )
            popup.open()

    def delete_fighter(self, index):
        #Удаление бойца
        if 0 <= index < len(self.fighters):
            returned_points = self.fighters[index]['total_cost']
            self.points = str(int(self.points) + returned_points)
            del self.fighters[index]
            self.update_display()

    def proceed_to_abilities(self):
        #Возврат к экрану способностей
        self.manager.current = 'abilities'

    def proceed_to_main(self):
        #Возврат на главный экран
        self.manager.current = 'main'

    def show_error(self, message):
        #Показать сообщение об ошибке
        from kivy.uix.popup import Popup
        from kivy.uix.label import Label
        Popup(title='Ошибка', content=Label(text=message), size_hint=(0.6, 0.3)).open()

    def export_to_pdf(self):
        try:
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.units import cm
            import os

            # 1. Подготовка файла
            band_name_ascii = ''.join([c if ord(c) < 128 else '_' for c in self.band_name])
            filename = f"{band_name_ascii}_отряд.pdf"
            filepath = os.path.join(os.path.expanduser("~"), "Downloads", filename)

            # 2. Регистрация шрифтов
            try:
                font_path = 'C:/Windows/Fonts/times.ttf'
                if os.path.exists(font_path):
                    pdfmetrics.registerFont(TTFont('Times-Roman', font_path))
                    pdfmetrics.registerFont(TTFont('Times-Bold', 'C:/Windows/Fonts/timesbd.ttf'))
                    normal_font = 'Times-Roman'
                    bold_font = 'Times-Bold'
                else:
                    # Альтернативный вариант - DejaVu Sans
                    try:
                        pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))
                        pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', 'DejaVuSans-Bold.ttf'))
                        normal_font = 'DejaVuSans'
                        bold_font = 'DejaVuSans-Bold'
                    except:
                        # Стандартные шрифты ReportLab
                        normal_font = 'Helvetica'
                        bold_font = 'Helvetica-Bold'
            except Exception as font_error:
                print(f"Ошибка шрифтов: {font_error}")
                normal_font = 'Helvetica'
                bold_font = 'Helvetica-Bold'

            # 3. Создание стилей
            styles = getSampleStyleSheet()

            title_style = ParagraphStyle(
                'Title',
                parent=styles['Heading1'],
                fontName=bold_font,
                fontSize=18,
                alignment=TA_CENTER,
                spaceAfter=12,
                leading=18
            )

            subtitle_style = ParagraphStyle(
                'Subtitle',
                parent=styles['Heading2'],
                fontName=bold_font,
                fontSize=14,
                alignment=TA_LEFT,
                spaceAfter=10,
                leading=14
            )

            normal_style = ParagraphStyle(
                'Normal',
                parent=styles['Normal'],
                fontName=normal_font,
                fontSize=12,
                leading=14,
                spaceAfter=6,
                alignment=TA_LEFT
            )

            bold_style = ParagraphStyle(
                'Bold',
                parent=styles['Heading3'],
                fontName=bold_font,
                fontSize=12,
                leading=14,
                spaceAfter=6,
                alignment=TA_LEFT
            )

            section_style = ParagraphStyle(
                'Section',
                parent=styles['Heading2'],
                fontName=bold_font,
                fontSize=12,
                leading=12,
                spaceBefore=6,  # Отступ перед заголовком
                spaceAfter=0,  # Без отступа после заголовка
                alignment=TA_LEFT,
                keepWithNext=1  # Удерживать вместе со следующим элементом
            )

            # 4. Создание PDF
            c = canvas.Canvas(filepath, pagesize=A4)
            width, height = A4
            margin = 2 * cm
            y_position = height - margin

            # 5. Заголовок и информация об очках
            title = Paragraph(f"<b>{self.band_name}</b>", title_style)
            title.wrap(width - margin * 2, height)
            title.drawOn(c, margin, y_position)
            y_position -= title.height + 0.3 * cm

            fighters_cost = sum(f.get('total_cost', 0) for f in self.fighters)
            initial_points = int(self.points) + fighters_cost
            points_text = f"Потрачено очков: {fighters_cost} из {initial_points}"
            points = Paragraph(points_text, subtitle_style)
            points.wrap(width - margin * 2, height)
            points.drawOn(c, margin, y_position)
            y_position -= points.height + 0.8 * cm

            # 6. Список бойцов
            for fighter in self.fighters:
                # Проверка места на странице перед началом нового бойца
                estimated_fighter_height = 4 * cm  # Минимальная оценка высоты бойца
                if y_position - estimated_fighter_height < margin:
                    c.showPage()
                    y_position = height - margin

                # Имя и тип бойца
                fighter_title = Paragraph(
                    f"<b>{fighter['name']}</b> - {fighter['type']} ({fighter['total_cost']} очков)",
                    bold_style
                )
                fighter_title.wrap(width - margin * 2, height)
                fighter_title.drawOn(c, margin, y_position)
                y_position -= fighter_title.height + 0.2 * cm

                # Характеристики (КП, ОД)
                stats = Paragraph(
                    f"КП: {fighter['stats']['КП']}, ОД: {fighter['stats']['ОД']}",
                    normal_style
                )
                stats.wrap(width - margin * 2, height)
                stats.drawOn(c, margin, y_position)
                y_position -= stats.height + 0.3 * cm

                # Способности
                if fighter['abilities']:
                    abilities_title = Paragraph("<b>Способности:</b>", section_style)
                    abilities_title.wrap(width - margin * 2, height)
                    abilities_title.drawOn(c, margin, y_position)
                    y_position -= abilities_title.height + 0.1 * cm

                    for ability in fighter['abilities']:
                        ability_text = Paragraph(
                            f"• {ability['Название']}: {ability.get('Описание', '')}",
                            normal_style
                        )
                        ability_text.wrap(width - margin * 2, height)

                        if y_position - ability_text.height < margin:
                            c.showPage()
                            y_position = height - margin
                            abilities_title = Paragraph("<b>Способности (продолжение):</b>", section_style)
                            abilities_title.wrap(width - margin * 2, height)
                            abilities_title.drawOn(c, margin, y_position)
                            y_position -= abilities_title.height + 0.1 * cm

                        ability_text.drawOn(c, margin + 0.5 * cm, y_position - ability_text.height)
                        y_position -= ability_text.height + 0.1 * cm

                # Предметы
                if fighter['equipment']:
                    # Отступ перед разделом предметов
                    y_position -= 0.5 * cm

                    items_title = Paragraph("<b>Предметы:</b>", section_style)
                    items_title.wrap(width - margin * 2, height)
                    items_title.drawOn(c, margin, y_position)
                    y_position -= items_title.height + 0.1 * cm

                    for item in fighter['equipment']:
                        item_desc = []
                        if 'Куб' in item: item_desc.append(f"Куб: {item['Куб']}")
                        if 'Эффект крита' in item: item_desc.append(f"Крит: {item['Эффект крита']}")
                        if 'Свойства' in item: item_desc.append(f"Свойства: {item['Свойства']}")

                        item_text = Paragraph(
                            f"<b>{item['Название']}</b> ({item.get('Цена', 0)} очков): {', '.join(item_desc)}",
                            normal_style
                        )
                        item_text.wrap(width - margin * 2, height)

                        if y_position - item_text.height < margin:
                            c.showPage()
                            y_position = height - margin
                            items_title = Paragraph("<b>Предметы (продолжение):</b>", section_style)
                            items_title.wrap(width - margin * 2, height)
                            items_title.drawOn(c, margin, y_position)
                            y_position -= items_title.height + 0.1 * cm

                        item_text.drawOn(c, margin, y_position - item_text.height)
                        y_position -= item_text.height + 0.1 * cm

                # Отступ между бойцами
                y_position -= 1.0 * cm

            # 7. Отрядные способности (с проверкой места)
            if self.abilities:
                # Проверяем, достаточно ли места для заголовка и хотя бы одной способности
                sample_ability = self.abilities[0]
                sample_text = Paragraph(
                    f"<b>{sample_ability}</b>: {ABILITIES.get(sample_ability, '')}",
                    normal_style
                )
                sample_text.wrap(width - margin * 2, height)

                abilities_title = Paragraph("<b>Отрядные способности:</b>", section_style)
                abilities_title.wrap(width - margin * 2, height)

                required_space = abilities_title.height + sample_text.height + 1.0 * cm

                if y_position - required_space < margin:
                    c.showPage()
                    y_position = height - margin

                # Рисуем заголовок с отступом
                y_position -= 0.5 * cm
                abilities_title.drawOn(c, margin, y_position)
                y_position -= abilities_title.height + 0.3 * cm

                # Рисуем способности
                for ability in self.abilities:
                    ability_text = Paragraph(
                        f"<b>{ability}</b>: {ABILITIES.get(ability, '')}",
                        normal_style
                    )
                    ability_text.wrap(width - margin * 2, height)

                    if y_position - ability_text.height < margin:
                        c.showPage()
                        y_position = height - margin
                        abilities_title = Paragraph("<b>Отрядные способности (продолжение):</b>", section_style)
                        abilities_title.wrap(width - margin * 2, height)
                        abilities_title.drawOn(c, margin, y_position)
                        y_position -= abilities_title.height + 0.3 * cm

                    ability_text.drawOn(c, margin, y_position - ability_text.height)
                    y_position -= ability_text.height + 0.3 * cm

            # 8. Сохранение PDF
            c.save()

            # 9. Уведомление об успехе
            from kivy.uix.popup import Popup
            from kivy.uix.label import Label
            Popup(
                title='Готово',
                content=Label(text=f"PDF успешно сохранен:\n{filepath}"),
                size_hint=(0.8, 0.3)
            ).open()

        except Exception as e:
            # 10. Обработка ошибок
            from kivy.uix.popup import Popup
            from kivy.uix.label import Label
            error_msg = f"Ошибка при создании PDF:\n{str(e)}"
            Popup(
                title='Ошибка',
                content=Label(text=error_msg),
                size_hint=(0.8, 0.3)
            ).open()
            print(error_msg)


class AddFighterPopup(Popup):
    def __init__(self, callback, edit_mode=False, fighter_data=None, **kwargs):
        super().__init__(**kwargs)
        self.callback = callback
        self.edit_mode = edit_mode
        self.fighter_data = fighter_data
        self.selected_type = None
        self.abilities_data = []
        self.equipment_data = []
        self.load_data()
        Clock.schedule_once(self._setup_ui)
        self.current_selection = None

    def load_data(self):
        try:
            with open('abilities.json', 'r', encoding='utf-8') as f:
                self.abilities_data = json.load(f).get('Способности', [])

            with open('items.json', 'r', encoding='utf-8') as f:
                self.equipment_data = json.load(f).get('Предметы', [])
        except Exception as e:
            print(f"Ошибка загрузки данных: {e}")
            self.abilities_data = []
            self.equipment_data = []

    def _setup_ui(self, dt):
        if not self.type_spinner:
            return

        self.type_spinner.values = list(CHARACTER_TYPE.keys())

        # Если это режим редактирования, заполняем поля
        if self.edit_mode and self.fighter_data:
            self.fighter_name.text = self.fighter_data['name']
            self.type_spinner.text = self.fighter_data['type']
            self.selected_type = self.fighter_data['type']

            # Обновляем спиннеры способностей и предметов
            self.update_abilities_spinners()
            self.update_equipment_spinners()

            # Устанавливаем выбранные способности
            for i, ability in enumerate(self.fighter_data['abilities']):
                if ability['Название'] != 'Животное' or self.selected_type != 'Собака':
                    for child in self.abilities_layout.children:
                        if isinstance(child, Spinner) and i < len(self.fighter_data['abilities']):
                            child.text = ability['Название']

            # Устанавливаем выбранные предметы
            for i, item in enumerate(self.fighter_data['equipment']):
                for child in self.equipment_layout.children:
                    if isinstance(child, Spinner) and child.text.startswith(f'Слот {i + 1}'):
                        child.text = item['Название']

            self.update_total_cost_display()

    def on_type_selected(self, spinner, text):
        self.selected_type = text
        self.update_abilities_spinners()
        self.update_equipment_spinners()
        self.update_total_cost_display()

    def update_abilities_spinners(self):
        if not self.abilities_layout:
            return

        self.abilities_layout.clear_widgets()
        self.abilities_layout.add_widget(Label(text="Способности:", size_hint_y=None, height=30))

        if not self.selected_type:
            return

        char_type = CHARACTER_TYPE.get(self.selected_type, {})
        abilities_count = char_type.get('abilities_count', 0)

        # Если это собака, добавляем автоматическую способность
        if self.selected_type == 'Собака' and 'default_ability' in char_type:
            default_ability = char_type['default_ability']
            ability_label = Label(
                text=f"{default_ability} (автоматически)",
                size_hint_y=None,
                height=40,
            )
            self.abilities_layout.add_widget(ability_label)

        # Добавляем спиннеры для выбора способностей
        for _ in range(abilities_count):
            spinner = Spinner(
                text='Выберите способность',
                values=['Выберите способность'] + [ab['Название'] for ab in self.abilities_data],
                size_hint=(None, None),
                size=(300, 44),
                pos_hint={'center_x': 0.5}
            )
            spinner.bind(text=lambda instance, value: self.update_total_cost_display())
            self.abilities_layout.add_widget(spinner)

    def update_equipment_spinners(self):
        if not self.equipment_layout:
            return

        self.equipment_layout.clear_widgets()
        self.equipment_layout.add_widget(Label(text="Предметы (4 слота):", size_hint_y=None, height=30))

        for i in range(4):
            spinner = Spinner(
                text=f'Слот {i + 1} - выберите предмет',
                values=[''] + [item['Название'] for item in self.equipment_data],
                size_hint=(None, None),
                size=(300, 44),
                pos_hint={'center_x': 0.5}
            )
            spinner.bind(text=lambda instance, value: self.update_total_cost_display())
            self.equipment_layout.add_widget(spinner)

    def update_total_cost_display(self):
        if hasattr(self, 'ids') and 'total_cost_label' in self.ids:
            self.ids.total_cost_label.text = f"Общая стоимость: {self.calculate_total_cost()} очков"

    def calculate_total_cost(self):
        if not self.selected_type:
            return 0

        total = CHARACTER_TYPE.get(self.selected_type, {}).get('point_cost', 0)

        for ability in self._get_selected_abilities():
            if not (self.selected_type == 'Собака' and ability['Название'] == 'Животное'):
                total += ability.get('Цена', 0)

        for item in self._get_selected_equipment():
            total += item.get('Цена', 0)

        return total

    def _get_selected_abilities(self):
        #Получение выбранных способностей без дублирования для собак
        selected = []

        # Для собак добавляем способность только если её нет в выбранных
        if self.selected_type == 'Собака':
            default_ability = {
                'Название': 'Животное',
                'Тип': 'Особое',
                'Описание': 'Стандартная способность для животных',
                'Ограничения': '',
                'Цена': 0
            }

            # Проверяем, не добавлена ли уже эта способность
            ability_exists = False
            for child in self.abilities_layout.children:
                if isinstance(child, Spinner) and child.text == 'Животное':
                    ability_exists = True
                    break

            if not ability_exists:
                selected.append(default_ability)

        # Добавляем выбранные способности
        for child in self.abilities_layout.children:
            if isinstance(child, Spinner) and child.text != 'Выберите способность':
                ability = next((ab for ab in self.abilities_data if ab['Название'] == child.text), None)
                if ability and ability['Название'] != 'Животное':  # Исключаем повторное добавление
                    selected.append(ability)

        return selected

    def _get_selected_equipment(self):
        selected = []
        if not self.equipment_layout:
            return selected

        for child in self.equipment_layout.children:
            if isinstance(child, Spinner) and child.text and not child.text.startswith('Слот'):
                item = next((it for it in self.equipment_data if it['Название'] == child.text), None)
                if item:
                    selected.append(item)
        return selected

    def add_fighter(self):
        if not self.fighter_name.text.strip() or not self.selected_type:
            self.show_error("Введите имя и выберите тип")
            return

        total_cost = self.calculate_total_cost()
        generator_screen = App.get_running_app().root.get_screen('generator')

        try:
            available_points = int(generator_screen.points)
            if total_cost > available_points:
                self.show_error(f"Недостаточно очков! Нужно {total_cost}, доступно {available_points}")
                return
        except (ValueError, AttributeError):
            self.show_error("Ошибка проверки очков")
            return

        fighter_data = {
            'name': self.fighter_name.text,
            'type': self.selected_type,
            'stats': CHARACTER_TYPE[self.selected_type],
            'abilities': self._get_selected_abilities(),
            'equipment': self._get_selected_equipment(),
            'total_cost': total_cost
        }

        self.callback(fighter_data)
        self.dismiss()

    def update_abilities_spinners(self):
        if not self.abilities_layout:
            return

        self.abilities_layout.clear_widgets()
        self.abilities_layout.add_widget(Label(text="Способности:", size_hint_y=None, height=30))

        if not self.selected_type:
            return

        char_type = CHARACTER_TYPE.get(self.selected_type, {})
        abilities_count = char_type.get('abilities_count', 0)

        # Если это собака, добавляем автоматическую способность
        if self.selected_type == 'Собака' and 'default_ability' in char_type:
            default_ability = {
                'Название': 'Животное',
                'Тип': 'Особое',
                'Описание': 'Стандартная способность для животных',
                'Ограничения': '',
                'Цена': 0
            }
            ability_label = Label(
                text=f"{default_ability['Название']} (автоматически)",
                size_hint_y=None,
                height=40,
            )
            self.abilities_layout.add_widget(ability_label)

        # Добавляем спиннеры для выбора способностей
        for i in range(abilities_count):
            spinner = Spinner(
                text='Выберите способность',
                values=['Выберите способность'] + [ab['Название'] for ab in self.abilities_data],
                size_hint=(None, None),
                size=(300, 44),
                pos_hint={'center_x': 0.5}
            )
            spinner.bind(text=self.on_ability_selected)
            self.abilities_layout.add_widget(spinner)

    def update_equipment_spinners(self):
        if not self.equipment_layout:
            return

        self.equipment_layout.clear_widgets()
        self.equipment_layout.add_widget(Label(text="Предметы (4 слота):", size_hint_y=None, height=30))

        for i in range(4):
            spinner = Spinner(
                text=f'Слот {i + 1} - выберите предмет',
                values=[''] + [item['Название'] for item in self.equipment_data],
                size_hint=(None, None),
                size=(300, 44),
                pos_hint={'center_x': 0.5}
            )
            spinner.bind(text=self.on_item_selected)
            self.equipment_layout.add_widget(spinner)

    def on_ability_selected(self, spinner, text):
        if text and text != 'Выберите способность':
            ability = next((ab for ab in self.abilities_data if ab['Название'] == text), None)
            if ability:
                popup = ItemAbilityPopup(ability, is_ability=True)
                popup.bind(on_dismiss=lambda x: self._handle_selection_result(spinner, popup))
                popup.open()
            else:
                spinner.text = 'Выберите способность'

    def on_item_selected(self, spinner, text):
        if text and not text.startswith('Слот'):
            item = next((it for it in self.equipment_data if it['Название'] == text), None)
            if item:
                popup = ItemAbilityPopup(item, is_ability=False)
                popup.bind(on_dismiss=lambda x: self._handle_selection_result(spinner, popup))
                popup.open()
            else:
                spinner.text = f'Слот {self.get_slot_number(spinner)} - выберите предмет'

    def _handle_selection_result(self, spinner, popup):
        if not popup.confirmed:
            # Если нажали "Отменить", сбрасываем выбор
            if popup.is_ability:
                spinner.text = 'Выберите способность'
            else:
                spinner.text = f'Слот {self.get_slot_number(spinner)} - выберите предмет'
        self.update_total_cost_display()

    def get_slot_number(self, spinner):
        # Получаем номер слота из текста спиннера
        for i, child in enumerate(self.equipment_layout.children):
            if isinstance(child, Spinner) and child == spinner:
                return len(self.equipment_layout.children) - i
        return 1

    def confirm_selection(self, item_data):
        if self.current_selection:
            if self.current_selection['type'] == 'ability':
                self.current_selection['spinner'].text = item_data['Название']
            else:
                slot_num = self.get_slot_number(self.current_selection['spinner'])
                self.current_selection['spinner'].text = item_data['Название']

            self.update_total_cost_display()
        self.current_selection = None

    def show_error(self, message):
        popup = Popup(title='Ошибка',
                     content=Label(text=message),
                     size_hint=(0.6, 0.3))
        popup.open()


class ItemAbilityPopup(Popup):
    def __init__(self, item_data, is_ability=True, **kwargs):
        super().__init__(**kwargs)
        self.title = item_data['Название']
        self.size_hint = (0.8, 0.8)
        self.auto_dismiss = False
        self.item_data = item_data
        self.is_ability = is_ability
        self.confirmed = False

        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Основная информация
        info_text = self._generate_info_text(item_data)
        info = Label(
            text=info_text,
            size_hint_y=0.8,
            markup=True,
            halign='left',
            valign='top',
            text_size=(self.width * 5, None)
        )

        # Кнопки
        btn_layout = BoxLayout(size_hint_y=0.1, spacing=5)
        btn_add = Button(text='Добавить')
        btn_add.bind(on_press=self.on_confirm)
        btn_cancel = Button(text='Отменить')
        btn_cancel.bind(on_press=self.dismiss)

        btn_layout.add_widget(btn_add)
        btn_layout.add_widget(btn_cancel)

        layout.add_widget(info)
        layout.add_widget(btn_layout)

        self.content = layout

    def _generate_info_text(self, item_data):
        if self.is_ability:
            return (
                f"[b]Тип:[/b] {item_data.get('Тип', '')}\n\n"
                f"[b]Описание:[/b]\n{item_data.get('Описание', '')}\n\n"
                f"[b]Ограничения:[/b]\n{item_data.get('Ограничения', 'Нет')}\n\n"
                f"[b]Цена:[/b] {item_data.get('Цена', 0)} очков"
            )
        else:
            return (
                f"[b]Куб:[/b] {item_data.get('Куб', '')}\n\n"
                f"[b]Эффект крита:[/b] {item_data.get('Эффект крита', '')}\n\n"
                f"[b]Свойства:[/b]\n{item_data.get('Свойства', '')}\n\n"
                f"[b]Цена:[/b] {item_data.get('Цена', 0)} очков"
            )

    def on_confirm(self, instance):
        self.confirmed = True
        self.dismiss()

class EisenhutBandGeneratorApp(App):
    def build(self):
        # Установка размера окна (ширина, высота)
        Window.size = (1200, 800)
        sm = ScreenManager(transition=FadeTransition())
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(AbilitySelectionScreen(name='abilities'))
        sm.add_widget(GeneratorScreen(name='generator'))
        return sm


if __name__ == '__main__':
    EisenhutBandGeneratorApp().run()