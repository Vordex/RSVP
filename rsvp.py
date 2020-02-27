import base64
import database
import fitz
from io import BytesIO
import zipfile


settings = database.Settings()
progress = 0


class File:
    def __init__(self, file, final_path=None, final_name=None, existing=True):
        self.file = file

        filename = self.file.split(".")[0]

        if final_name is None:
            final_name = filename

        self.pre_file = self.file

        if not existing:
            self.file = f"{final_path}/{final_name}.rsvp"
            self.create()

    def create(self):
        global progress

        print(self.file)

        file_zip = zipfile.ZipFile(self.file, "w", compression=zipfile.ZIP_DEFLATED)

        with file_zip as zip_file:
            print(self.pre_file)
            document = fitz.Document(self.pre_file)

            zip_file.writestr("info.txt", f"{document.metadata['title']}\n{document.metadata['author']}\n0")
            first_page = document.loadPage()
            pix = first_page.getPixmap()
            zip_file.writestr("images/cover.png", base64.decodebytes(base64.b64encode(pix.getPNGdata())))

            images_count = 0
            words = ""
            images = []

            number_pages = document.pageCount

            pages_count = 0

            for page in document.pages():
                for block in page.getText("dict")["blocks"]:
                    print(block)
                    if block["type"] == 0:
                        for line in block["lines"]:
                            for span in line["spans"]:
                                for word in span["text"].split():
                                    words = f"{words}\n{word}"
                    else:
                        if base64.decodebytes(base64.b64encode(block["image"])) in images:
                            words = f"{words}\nimage: image{images.index(base64.decodebytes(base64.b64encode(block['image'])))}.png"
                        else:
                            images.append(base64.decodebytes(base64.b64encode(block["image"])))
                            words = f"{words}\nimage: image{images_count}.png"
                            zip_file.writestr(
                                f"images/image{images_count}.png",
                                base64.decodebytes(base64.b64encode(block["image"]))
                            )

                            images_count += 1

                pages_count += 1
                progress = int(100 / number_pages * pages_count)

            zip_file.writestr("content.txt", words[1:])

    def get_info(self):
        _info = {}

        with zipfile.ZipFile(self.file) as zip_file:
            with zip_file.open("info.txt") as info:
                lines = info.readlines()
                _info["name"] = lines[0].decode("utf-8").replace("\n", "")
                _info["author"] = lines[1].decode("utf-8").replace("\n", "")
                _info["starting point"] = int(lines[2].decode("utf-8").replace("\n", ""))

        return _info

    def read_lines(self):
        with zipfile.ZipFile(self.file) as zip_file:
            with zip_file.open("content.txt") as content:
                words = []
                for word in content.readlines():
                    words.append(word.decode("utf-8").replace("\n", ""))

        return words

    def get_image(self, image):
        with zipfile.ZipFile(self.file) as zip_file:
            with zip_file.open(f"images/{image}") as file:
                _image = BytesIO(base64.decodebytes(base64.b64encode(file.read())))

        return _image
