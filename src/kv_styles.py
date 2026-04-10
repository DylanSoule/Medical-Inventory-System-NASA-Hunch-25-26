"""
Medical Inventory System - Kivy KV Language Definitions

All UI layout / style strings live here so the Python modules
stay focused on logic.

Sections:
    1. Imports
    2. Base Themed Widgets (Label, Button, Danger, Success)
    3. Numpad Widget
    4. Popups (Message, Confirm, Input, Virtual Keyboard, Choice)
    5. Table Components (DataRow, HeaderRow)
    6. Main Screen (Sidebar: Search/Filters/Actions | Content: Data Table)
    7. History Screen
    8. Personal Database Screen
"""

KV = """
# ============================================================
# 1. IMPORTS
# ============================================================
#:import dp kivy.metrics.dp

# ============================================================
# 2. BASE THEMED WIDGETS
# ============================================================

# -- Standard label with white text --
<ThemedLabel@Label>:
    font_size: dp(16)
    color: 1, 1, 1, 1

# -- Standard button (blue) --
<ThemedButton@Button>:
    font_size: dp(16)
    size_hint_y: None
    height: dp(50)
    background_color: 0.24, 0.51, 0.78, 1
    background_normal: ''

# -- Danger button (red) --
<DangerButton@ThemedButton>:
    background_color: 0.7, 0.13, 0.13, 1

# -- Success button (green) --
<SuccessButton@ThemedButton>:
    background_color: 0.13, 0.77, 0.37, 1

# ============================================================
# 3. NUMPAD WIDGET (reusable on-screen number pad)
# ============================================================
<NumpadWidget>:
    cols: 3
    spacing: dp(8)
    size_hint_y: None
    height: dp(280)

# ============================================================
# 4. POPUPS
# ============================================================

# ------------------------------------------------------------
# 4a. Message Popup — simple dismissable alert
# ------------------------------------------------------------
<MessagePopup>:
    size_hint: 0.5, 0.4
    auto_dismiss: True
    BoxLayout:
        orientation: 'vertical'
        padding: dp(20)
        spacing: dp(15)
        canvas.before:
            Color:
                rgba: 0.16, 0.16, 0.18, 1
            RoundedRectangle:
                pos: self.pos
                size: self.size
                radius: [dp(12)]
        Label:
            text: root.message
            font_size: dp(16)
            text_size: self.width, None
            halign: 'center'
            valign: 'middle'
            size_hint_y: 0.7
        ThemedButton:
            text: 'OK'
            on_release: root.dismiss()
            size_hint_x: 0.5
            pos_hint: {'center_x': 0.5}

# ------------------------------------------------------------
# 4b. Confirm Popup — Yes / No confirmation dialog
# ------------------------------------------------------------
<ConfirmPopup>:
    size_hint: 0.5, 0.4
    auto_dismiss: False
    BoxLayout:
        orientation: 'vertical'
        padding: dp(20)
        spacing: dp(15)
        canvas.before:
            Color:
                rgba: 0.16, 0.16, 0.18, 1
            RoundedRectangle:
                pos: self.pos
                size: self.size
                radius: [dp(12)]
        Label:
            text: root.message
            font_size: dp(16)
            text_size: self.width, None
            halign: 'center'
            valign: 'middle'
            size_hint_y: 0.6
        BoxLayout:
            size_hint_y: 0.4
            spacing: dp(12)
            ThemedButton:
                text: 'Yes'
                on_release: root.on_yes()
            DangerButton:
                text: 'No'
                on_release: root.on_no()

# ------------------------------------------------------------
# 4c. Input Popup — barcode / amount / admin / date entry
#     Includes numpad for touch-friendly number input
# ------------------------------------------------------------
<InputPopup>:
    size_hint: 0.55, 0.75
    auto_dismiss: False
    BoxLayout:
        orientation: 'vertical'
        padding: dp(15)
        spacing: dp(10)
        canvas.before:
            Color:
                rgba: 0.16, 0.16, 0.18, 1
            RoundedRectangle:
                pos: self.pos
                size: self.size
                radius: [dp(12)]

        # -- Prompt label --
        Label:
            text: root.prompt
            font_size: dp(18)
            size_hint_y: None
            height: dp(40)

        # -- Text input field --
        TextInput:
            id: input_field
            text: root.input_text
            font_size: dp(20)
            size_hint_y: None
            height: dp(50)
            multiline: False
            password: root.is_password
            on_text: root.input_text = self.text
            on_text_validate: root.on_ok()

        # -- Numpad grid --
        NumpadWidget:
            id: numpad
            on_key: root.on_numpad_key(args[1])

        # -- OK / Cancel buttons --
        BoxLayout:
            size_hint_y: None
            height: dp(50)
            spacing: dp(12)
            ThemedButton:
                text: 'OK'
                on_release: root.on_ok()
            Button:
                text: 'Cancel'
                font_size: dp(16)
                size_hint_y: None
                height: dp(50)
                background_color: 0.35, 0.35, 0.35, 1
                background_normal: ''
                on_release: root.on_cancel()

# ------------------------------------------------------------
# 4d. Virtual Keyboard Popup — full alpha-numeric keyboard
# ------------------------------------------------------------
<VirtualKeyboardPopup>:
    size_hint: 0.85, 0.8
    auto_dismiss: False
    BoxLayout:
        orientation: 'vertical'
        padding: dp(15)
        spacing: dp(8)
        canvas.before:
            Color:
                rgba: 0.16, 0.16, 0.18, 1
            RoundedRectangle:
                pos: self.pos
                size: self.size
                radius: [dp(12)]

        # -- Prompt label --
        Label:
            text: root.prompt
            font_size: dp(18)
            size_hint_y: None
            height: dp(35)

        # -- Text input field --
        TextInput:
            id: kb_input
            text: root.input_text
            font_size: dp(18)
            size_hint_y: None
            height: dp(48)
            multiline: False
            on_text: root.input_text = self.text

        # -- Keyboard rows (populated dynamically) --
        BoxLayout:
            id: keyboard_rows
            orientation: 'vertical'
            spacing: dp(4)
            size_hint_y: 0.65

        # -- OK / Cancel buttons --
        BoxLayout:
            size_hint_y: None
            height: dp(50)
            spacing: dp(12)
            SuccessButton:
                text: 'OK'
                on_release: root.on_ok()
            Button:
                text: 'Cancel'
                font_size: dp(16)
                size_hint_y: None
                height: dp(50)
                background_color: 0.35, 0.35, 0.35, 1
                background_normal: ''
                on_release: root.on_cancel()

# ------------------------------------------------------------
# 4e. Choice Popup — Restock / Use Item action selector
# ------------------------------------------------------------
<ChoicePopup>:
    size_hint: 0.5, 0.45
    auto_dismiss: False
    BoxLayout:
        orientation: 'vertical'
        padding: dp(20)
        spacing: dp(15)
        canvas.before:
            Color:
                rgba: 0.16, 0.16, 0.18, 1
            RoundedRectangle:
                pos: self.pos
                size: self.size
                radius: [dp(12)]

        # -- Title --
        Label:
            text: 'Select Action Type'
            font_size: dp(22)
            bold: True
            size_hint_y: None
            height: dp(40)

        # -- Description --
        Label:
            text: 'Choose whether to restock an item or log usage:'
            font_size: dp(15)
            text_size: self.width, None
            halign: 'center'
            size_hint_y: None
            height: dp(40)

        # -- Action buttons --
        BoxLayout:
            spacing: dp(12)
            size_hint_y: None
            height: dp(55)
            SuccessButton:
                text: 'Restock'
                on_release: root.choose('restock')
            ThemedButton:
                text: 'Use Item'
                on_release: root.choose('use')
            Button:
                text: 'Cancel'
                font_size: dp(16)
                size_hint_y: None
                height: dp(50)
                background_color: 0.35, 0.35, 0.35, 1
                background_normal: ''
                on_release: root.choose(None)

# ============================================================
# 5. TABLE COMPONENTS
# ============================================================

# -- Data Row — single selectable inventory row --
<DataRow>:
    size_hint_y: None
    height: dp(44)
    spacing: dp(2)
    canvas.before:
        Color:
            rgba: (0.24, 0.44, 0.65, 0.6) if self.selected else (0.17, 0.17, 0.17, 1)
        Rectangle:
            pos: self.pos
            size: self.size

# -- Header Row — column titles for data tables --
<HeaderRow>:
    size_hint_y: None
    height: dp(44)
    spacing: dp(2)
    canvas.before:
        Color:
            rgba: 0.25, 0.25, 0.28, 1
        Rectangle:
            pos: self.pos
            size: self.size

# ============================================================
# 6. MAIN SCREEN
# ============================================================
<MainScreen>:
    BoxLayout:
        orientation: 'vertical'
        canvas.before:
            Color:
                rgba: 0.11, 0.11, 0.12, 1
            Rectangle:
                pos: self.pos
                size: self.size

        # -- Title bar --
        Label:
            text: 'Medical Inventory System'
            font_size: dp(28)
            bold: True
            size_hint_y: None
            height: dp(60)

        BoxLayout:
            padding: dp(10)
            spacing: dp(10)

            # ------------------------------------------------
            # 6a. SIDEBAR
            # ------------------------------------------------
            BoxLayout:
                orientation: 'vertical'
                size_hint_x: 0.28
                spacing: dp(10)
                padding: dp(8)
                canvas.before:
                    Color:
                        rgba: 0.14, 0.14, 0.16, 1
                    RoundedRectangle:
                        pos: self.pos
                        size: self.size
                        radius: [dp(8)]

                # -- Pinned top: Search & Filters --
                BoxLayout:
                    orientation: 'vertical'
                    size_hint_y: None
                    height: self.minimum_height
                    spacing: dp(6)

                    # -- Search bar --
                    Label:
                        text: 'Search'
                        font_size: dp(16)
                        size_hint_y: None
                        height: dp(30)
                        halign: 'left'
                        text_size: self.width, None
                    BoxLayout:
                        size_hint_y: None
                        height: dp(42)
                        spacing: dp(6)
                        TextInput:
                            id: search_input
                            hint_text: 'Search all fields...'
                            font_size: dp(15)
                            multiline: False
                            size_hint_x: 0.8
                            on_text: root.apply_filters()
                        Button:
                            text: chr(0x2328)
                            font_size: dp(18)
                            size_hint_x: 0.2
                            background_normal: ''
                            background_color: 0.24, 0.51, 0.78, 1
                            on_release: root.show_search_keyboard()

                    # -- Expiration filter dropdown --
                    Label:
                        text: 'Filters'
                        font_size: dp(16)
                        size_hint_y: None
                        height: dp(30)
                        halign: 'left'
                        text_size: self.width, None
                    Spinner:
                        id: filter_spinner
                        text: 'All'
                        values: ['All', 'Expiring Soon', 'Expired']
                        size_hint_y: None
                        height: dp(42)
                        font_size: dp(15)
                        on_text: root.apply_filters()

                    # -- Low stock checkbox --
                    BoxLayout:
                        size_hint_y: None
                        height: dp(36)
                        spacing: dp(6)
                        CheckBox:
                            id: low_stock_cb
                            size_hint_x: None
                            width: dp(36)
                            active: False
                            on_active: root.apply_filters()
                        Label:
                            text: 'Show low stock only'
                            font_size: dp(14)
                            halign: 'left'
                            text_size: self.width, None
                
                #sidebar med type filter
                    Label:
                        size_hint_y: None
                        height: dp(10)
                        text: 'Medication Types'
                    BoxLayout:
                        id: table_view_buttons
                        orientation: 'horizontal'
                        size_hint_y: None
                        height: dp(90)
                        spacing: dp(4)
                    BoxLayout:
                        id: table_view_dropdown
                        orientation: 'vertical'
                        size_hint_y: None
                        height: dp(90)
                
                #Spacer
                Widget:

                # -- Action buttons --
                BoxLayout:
                    orientation: 'vertical'
                    size_hint_y: None
                    height: dp(330)
                    spacing: dp(8)
                    padding: [0, dp(6)]

                    ThemedButton:
                        id: log_btn
                        text: 'Log Item Use'
                        on_release: root.log_item_use()
                    ThemedButton:
                        id: personal_btn
                        text: 'View Personal Database'
                        on_release: root.personal_run()
                    ThemedButton:
                        text: 'Delete Selected'
                        on_release: root.delete_selected()
                    ThemedButton:
                        text: 'View History'
                        on_release: root.show_history()
                    DangerButton:
                        text: 'Quit'
                        on_release: app.stop()

            # ------------------------------------------------
            # 6b. CONTENT AREA — Data Table
            # ------------------------------------------------
            BoxLayout:
                orientation: 'vertical'
                canvas.before:
                    Color:
                        rgba: 0.14, 0.14, 0.16, 1
                    RoundedRectangle:
                        pos: self.pos
                        size: self.size
                        radius: [dp(10)]

                # -- Per-column filter inputs --
                BoxLayout:
                    id: column_filters
                    orientation: 'horizontal'
                    size_hint_y: None
                    height: dp(40)
                    spacing: dp(4) 
                    
                    

                # -- Table header --
                HeaderRow:
                    id: header_row

                # -- Scrollable table body --
                ScrollView:
                    id: table_scroll
                    GridLayout:
                        id: table_body
                        cols: 1
                        size_hint_y: None
                        height: self.minimum_height
                        spacing: dp(1)
                        padding: dp(2)

# ============================================================
# 7. HISTORY SCREEN
# ============================================================
<HistoryScreen>:
    BoxLayout:
        orientation: 'vertical'
        padding: dp(10)
        spacing: dp(10)
        canvas.before:
            Color:
                rgba: 0.11, 0.11, 0.12, 1
            Rectangle:
                pos: self.pos
                size: self.size

        # -- Top bar: Pattern Recognition & Close --
        BoxLayout:
            size_hint_y: None
            height: dp(55)
            spacing: dp(10)
            ThemedButton:
                text: 'Pattern Recognition'
                on_release: root.show_pattern_rec()
                size_hint_x: 0.3
            Widget:
                size_hint_x: 0.4
            DangerButton:
                text: 'Close'
                on_release: root.go_back()
                size_hint_x: 0.3

        # -- History table header --
        HeaderRow:
            id: hist_header

        # -- Scrollable history rows --
        ScrollView:
            GridLayout:
                id: hist_body
                cols: 1
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(1)

# ============================================================
# 8. PERSONAL DATABASE SCREEN
# ============================================================
<PersonalScreen>:
    BoxLayout:
        orientation: 'vertical'
        padding: dp(8)
        spacing: dp(6)
        canvas.before:
            Color:
                rgba: 0.11, 0.11, 0.12, 1
            Rectangle:
                pos: self.pos
                size: self.size

        # -- Screen title --
        Label:
            id: title_label
            text: 'Personal Database'
            font_size: dp(24)
            bold: True
            size_hint_y: None
            height: dp(45)

        # -- Date navigation (previous / current / next) --
        BoxLayout:
            size_hint_y: None
            height: dp(42)
            spacing: dp(10)
            ThemedButton:
                text: '<< Previous Day'
                on_release: root.previous_day()
                size_hint_x: 0.25
            Label:
                id: date_label
                text: ''
                font_size: dp(18)
                bold: True
                size_hint_x: 0.5
            ThemedButton:
                text: 'Next Day >>'
                on_release: root.next_day()
                size_hint_x: 0.25

        # -- Scheduled Prescriptions section --
        Label:
            text: 'Scheduled Prescriptions'
            font_size: dp(16)
            bold: True
            size_hint_y: None
            height: dp(30)
            halign: 'left'
            text_size: self.width, None

        ScrollView:
            size_hint_y: 0.3
            GridLayout:
                id: presc_body
                cols: 1
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(1)

        # -- Usage History section --
        Label:
            text: 'Usage History (Today)'
            font_size: dp(16)
            bold: True
            size_hint_y: None
            height: dp(30)
            halign: 'left'
            text_size: self.width, None

        ScrollView:
            size_hint_y: 0.3
            GridLayout:
                id: hist_body
                cols: 1
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(1)

        # -- As-Needed Medications section --
        Label:
            text: 'As-Needed Medications'
            font_size: dp(16)
            bold: True
            size_hint_y: None
            height: dp(30)
            halign: 'left'
            text_size: self.width, None

        ScrollView:
            size_hint_y: 0.15
            GridLayout:
                id: as_needed_body
                cols: 1
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(1)

        # -- Bottom controls (Use Item / Today / Close) --
        BoxLayout:
            size_hint_y: None
            height: dp(46)
            spacing: dp(8)
            ThemedButton:
                text: 'Use Item'
                on_release: root.use_item_from_personal()
            SuccessButton:
                text: 'Today'
                on_release: root.goto_today()
            DangerButton:
                text: 'Close'
                on_release: root.go_back()
"""
