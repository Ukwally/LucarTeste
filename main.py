import os
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.popup import Popup
from kivy.uix.image import Image as KivyImage
from kivy.graphics.texture import Texture
from kivy.clock import Clock
from kivy.lang import Builder
import cv2
import pytesseract
from kivy.utils import platform

# Set the path for Tesseract-OCR
pytesseract.pytesseract.tesseract_cmd = r"/usr/bin/tesseract"  # Update path as necessary

os.environ['KIVY_NO_FILELOGO'] = '1'

# Load Kivy language string for layout
Builder.load_string("""
<CustomLoadingScreen>:
    orientation: 'vertical'
    padding: 10
    spacing: 10

    BoxLayout:
        size_hint_y: None
        height: '40dp'
        Button:
            background_color: 0, 1, 0, 1
            text: 'Usar Câmera'
            on_press: root.open_camera()
        Button:
            background_color: 0, 1, 0, 1
            text: 'Usar Áudio'
            on_press: root.open_audio()
        Button:
            background_color: 0, 1, 0, 1
            text: 'Abrir Galeria'
            on_press: root.open_gallery()

    Label:
        id: result_label
        text: ''  # Remover texto inicial aqui
        size_hint_y: None
        height: '40dp'
""")

class CustomLoadingScreen(BoxLayout):

    def __init__(self, **kwargs):
        super(CustomLoadingScreen, self).__init__(**kwargs)
        self.create_app_directories()
        self.create_app_directory()

    def create_app_directories(self):
        directories = [
            '/data/user/0/org.kvlucar.kvapplucar/files/app/_python_bundle/site-packages/kivy/data/logo',
            '/data/user/0/org.kvlucar.kvapplucar/files/app/.kivy/icon'
        ]

        for directory in directories:
            try:
                os.makedirs(directory, exist_ok=True)
                os.system(f'chmod -R 777 {directory}')
                print(f"Directory '{directory}' created with permissions set to 777.")
            except OSError as e:
                print(f"Error creating directory {directory}: {e}")

    def create_app_directory(self):
        external_storage = '/storage/emulated/0/Android/data/org.kvLucar.kvAppLucar/files'
        os.makedirs(external_storage, exist_ok=True)
        os.system(f'chmod -R 777 {external_storage}')
        print(f"Directory '{external_storage}' created with permissions set to 777.")

    def open_audio(self):
        App.get_running_app().show_popup('Abrir áudio ainda não está disponível')
        self.show_popup('Abrir áudio ainda não está disponível')

    def open_camera(self):
        self.capture = cv2.VideoCapture(0)
        if not self.capture.isOpened():
            self.show_popup('Câmera não disponível')
            return

        self.camera_popup = Popup(title='Capturar Imagem', size_hint=(0.9, 0.9))
        self.camera_layout = BoxLayout(orientation='vertical')
        self.camera_image = KivyImage()
        self.camera_layout.add_widget(self.camera_image)
        self.capture_button = Button(text='Capturar', size_hint_y=None, height='40dp')
        self.capture_button.bind(on_press=self.capture_image)
        self.camera_layout.add_widget(self.capture_button)
        self.camera_popup.content = self.camera_layout
        self.camera_popup.bind(on_dismiss=self.close_camera)
        self.camera_popup.open()
        Clock.schedule_interval(self.update_camera, 1.0 / 30.0)

    def update_camera(self, dt):
        ret, frame = self.capture.read()
        if ret:
            buf = cv2.flip(frame, 0).tobytes()
            image_texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
            image_texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
            self.camera_image.texture = image_texture

    def capture_image(self, *args):
        ret, frame = self.capture.read()
        if ret:
            external_storage = '/storage/emulated/0/Android/data/org.kvLucar.kvAppLucar/files'
            os.makedirs(external_storage, exist_ok=True)
            img_path = os.path.join(external_storage, 'captured_image.png')
            cv2.imwrite(img_path, frame)
            self.camera_popup.dismiss()
            self.preprocess_and_extract_text(img_path)
        else:
            self.show_popup('Erro ao capturar a imagem da câmera')

    def close_camera(self, *args):
        if self.capture:
            self.capture.release()
        Clock.unschedule(self.update_camera)
        self.capture = None  # Release the capture object

    def open_gallery(self):
        content = FileChooserListView(on_submit=self.process_image)
        popup = Popup(title="Escolher Imagem", content=content, size_hint=(0.9, 0.9))
        popup.open()

    def process_image(self, chooser, selection, touch):
        if selection:
            image_path = selection[0]
            self.preprocess_and_extract_text(image_path)

    def preprocess_and_extract_text(self, image_path):
        try:
            img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            if img is None:
                raise Exception("Erro ao abrir a imagem")

            _, img_bin = cv2.threshold(img, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
            processed_image_path = os.path.join(os.path.dirname(image_path), 'processed_image.png')
            cv2.imwrite(processed_image_path, img_bin)

            text = pytesseract.image_to_string(img_bin)

            result_label = self.ids.result_label  # Access the ID of CustomLoadingScreen
            result_label.text = text if text else "Nenhum texto encontrado"
        except Exception as e:
            self.show_popup(f'Erro ao extrair texto: {str(e)}')

    def show_popup(self, message):
        popup = Popup(title="Aviso", content=Label(text=message), size_hint=(0.6, 0.4))
        popup.open()

class MyApp(App):
    def build(self):
        self.root = CustomLoadingScreen()  # Set the initial screen
        return self.root

if __name__ == '__main__':
    MyApp().run()
