import base64
import zlib
import re
import numpy as np
from numpy import ndarray

class Payload:
    def __init__(self, img=None, compressionLevel=-1, xml=None):
        if compressionLevel < -1 or compressionLevel > 9:
            raise ValueError("Error: Compression Level should be between -1 and 9")
        self.compressionLevel = compressionLevel
        if img is None and xml is None:
            raise ValueError("Error: Need to fill fields img and/or xml")
        if (img is not None) and (type(img) != ndarray):
            raise TypeError("Error: img should be an instance of ndarray")
        if (xml is not None) and (type(xml) != str):
            raise TypeError("Error: xml should be a string")
        elif img is None:
            self.xml = xml
            self.img = self.construct_img()
        elif xml is None:
            self.img = img
            self.xml = self.construct_xml()

    def construct_img(self):
        re_type = re.search(r"<payload type=\"(.*?)\"", self.xml)
        if re_type:
            img_type = re_type.group(1)
        re_size = re.search(r"size=\"(\d*),(\d*)\"", self.xml)
        if re_size:
            rows = int(re_size.group(1))
            columns = int(re_size.group(2))
        re_compressed = re.search(r"compressed=\"(.*)\">", self.xml)
        if re_compressed:
            if re_compressed.group(1) == "True":
                compressed = True
            else:
                compressed = False
        re_payload = re.search(r"\n(.*)\n</payload>", self.xml)
        if re_payload:
            payload = re_payload.group(1)
        decoded_payload = base64.b64decode(payload)
        if compressed is True:
            decompressed_payload = zlib.decompress(bytes(decoded_payload))
        else:
            decompressed_payload = decoded_payload
        index = 0
        if img_type == "Gray":
            img = ndarray(shape=(rows, columns), dtype=int, order='C')
            for row in range(rows):
                for column in range(columns):
                    img[row, column] = decompressed_payload[index]
                    index += 1
        else:
            img = ndarray(shape=(rows, columns, 3), dtype=int, order='C')
            for color in range(3):
                for row in range(rows):
                    for column in range(columns):
                        img[row, column, color] = decompressed_payload[index]
                        index += 1
        return img

    def construct_xml(self):
        if self.compressionLevel == -1:
            compressed = False
            size = self.img.shape
            size_x = size[0]
            size_y = size[1]
            if len(size) > 2:
                payload_type = "Color"
                red = self.img[:, :, 0]
                green = self.img[:, :, 1]
                blue = self.img[:, :, 2]
                collapsed_img = np.concatenate((red.flatten('C'), green.flatten('C'), blue.flatten('C')), axis=0)
            else:
                payload_type = "Gray"
                collapsed_img = self.img.flatten('C')
            payload = base64.b64encode(bytes(collapsed_img))
        else:
            compressed = True
            size = self.img.shape
            size_x = size[0]
            size_y = size[1]
            if len(size) > 2:
                payload_type = "Color"
                red = self.img[:, :, 0]
                green = self.img[:, :, 1]
                blue = self.img[:, :, 2]
                collapsed_img = np.concatenate((red.flatten('C'), green.flatten('C'), blue.flatten('C')), axis=0)
            else:
                payload_type = "Gray"
                collapsed_img = self.img.flatten('C')
            compressed_payload = zlib.compress(bytes(collapsed_img), self.compressionLevel)
            payload = base64.b64encode(bytes(compressed_payload))
        xml = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n" \
              "<payload type=\"{0}\" size=\"{1},{2}\" compressed=\"{3}\">\n" \
              "{4}\n</payload>".format(payload_type, size_x, size_y, compressed, str(payload)[2:-1])
        return xml

class Carrier:
    def __init__(self, img):
        if type(img) != ndarray:
            raise TypeError("Error: img must be an instance of ndarray")
        self.img = img

    def payloadExists(self):
        power = 7
        byte = 0
        data = ""
        for pixel in range(40):
            if len(self.img.shape) > 2:
                bit = int(self.img[0, pixel, 0] % 2)
            else:
                bit = int(self.img[0, pixel] % 2)
            byte += bit*pow(2, power)
            power -= 1
            if power == -1:
                data += chr(byte)
                power = 7
                byte = 0
        if data == "<?xml":
            return True
        else:
            return False

    def clean(self):
        clean_img = np.copy(self.img)
        clean_img &= ~1
        return clean_img

    def embedPayload(self, payload, override=False):
        if override is False:
            if self.payloadExists() is True:
                raise Exception("Error: current carrier already contains a payload")
        if type(payload) != Payload:
            raise TypeError("Error: payload must be an instance of the Payload class")
        pixels_required = len(payload.xml)*8
        carrier_size = 1
        for dim in self.img.shape:
            carrier_size = carrier_size*dim
        if pixels_required > carrier_size:
            raise ValueError("Error: payload is too large for the carrier")
        shape = self.img.shape
        final_carrier = np.copy(self.img)
        payload_list = [ord(item) for item in list(payload.xml)]
        payload_bits = np.unpackbits(np.asarray(payload_list, dtype=np.uint8))
        row = 0
        column = 0
        color = 0
        if len(shape) == 2:
            for bit in payload_bits:
                if column >= shape[1]:
                    row += 1
                    column = 0
                final_carrier[row, column] &= ~1
                final_carrier[row, column] += int(bit)
                column += 1
        else:
            for bit in payload_bits:
                if column >= shape[1]:
                    row += 1
                    column = 0
                if row >= shape[0]:
                    color += 1
                    row = 0
                final_carrier[row, column, color] &= ~1
                final_carrier[row, column, color] += int(bit)
                column += 1
        return final_carrier

    def extractPayload(self):
        if self.payloadExists() is False:
            raise Exception("Error: carrier does not contain a payload")
        xml = ""
        shape = self.img.shape
        payload_bits = np.copy(self.img)
        payload_bits &= 1
        if len(shape) > 2:
            red = payload_bits[:, :, 0]
            green = payload_bits[:, :, 1]
            blue = payload_bits[:, :, 2]
            payload_buff = np.concatenate((red.flatten('C'), green.flatten('C'), blue.flatten('C')), axis=0)
            payload = np.packbits(payload_buff)
            payload_list = [chr(item) for item in payload]
            for item in payload_list:
                xml += item
                if item == '>':
                    termination = re.search(r"</payload>", xml)
                    if termination:
                        final_payload = Payload(None, -1, xml)
                        return final_payload
        else:
            payload = np.packbits(payload_bits)
            payload_list = [chr(item) for item in payload]
            for item in payload_list:
                xml += item
                if item == '>':
                    termination = re.search(r"</payload>", xml)
                    if termination:
                        final_payload = Payload(None, -1, xml)
                        return final_payload
