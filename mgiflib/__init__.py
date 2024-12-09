import struct
import math
from mgiflib.tables import ColorTable

class Extension:
    def __init__(self):
        self._label = 0
        self._bytes = None
        self._origin = 0
        self._wrtbl = False
        self._strm = None

    @property
    def label(self):
        return self._label

    @label.setter
    def label_set(self, value):
        if not self._wrtbl:
            raise ValueError
        self._strm.seek(self._origin)
        self._strm.write(struct.pack("<B",value))
        self._label = value
    
    @property
    def raw_data(self):
        return self._bytes
    
    @property
    def read(self,origin,length):
        return self._bytes[origin:(origin+length)]
    
    def write(self,origin,length,new_data):
        if not self._wrtbl:
            raise ValueError

        tgt = origin + self._origin+2
        strg = origin
        for i in range(length):
            if strg < len(self._bytes):
                self._bytes[strg] = new_data[strg]
                self._strm.seek(tgt)
                self._strm.write(struct.pack("<B",new_data[strg]))
            tgt+=1
            strg+=1

    def parse(self,strm,writeable):
        self._origin = strm.tell()
        self._strm = strm
        self._wrtbl = writeable
        self._label = strm.read(1)[0]
        leng = strm.read(1)[0]
        self._bytes = strm.read(leng)
        terminator = strm.read(1)
    
    def rebuild(self,strm):
        strm.write(struct.pack("<B",self._label))
        strm.write(struct.pack("<B",len(self._bytes)))
        strm.write(self._bytes)
        strm.write(b'\x00')

class ImageData:
    def __init__(self):
        self._origin = 0
        self._chain = []
        self._wrtbl = False
        self._strm = None
        self._min_code_size = 0
    
    @property
    def min_code_size(self):
        return self._min_code_size

    def parse(self,strm,writeable):
        self._wrtbl = writeable
        self._strm = strm
        self._origin = strm.tell()
        self._min_code_size = strm.read(1)[0]
        while True:
            org = strm.tell()
            lnn = strm.read(1)[0]
            if lnn == 0:
                break
            self._chain.append((org,lnn,strm.read(lnn)))
    def rebuild(self,strm):
        strm.write(struct.pack("<B",self._min_code_size))
        for org, lnn, dat in self._chain:
            strm.write(struct.pack("<B",lnn))
            strm.write(dat)
        strm.write(b'\x00')

class Image:
    def __init__(self):
        self._left = 0
        self._top = 0
        self._width = 0
        self._height = 0
        self._local_color_table = None
        self._origin = 0
        self._wrtbl = False
        self._strm = None
        self._memlocs = {}
        self._data = None

    @property
    def left(self):
        return self._left
    @property
    def top(self):
        return self._top
    @property
    def width(self):
        return self._width
    @property
    def height(self):
        return self._height
    @property
    def data(self):
        return self._data
    @property
    def local_color_table(self):
        return self._local_color_table

    @left.setter
    def left_setter(self,value):
        if not "left" in self._memlocs or not self._wrtbl:
            raise ValueError
        self._strm.seek(self._memlocs["left"])
        self._strm.write(struct.pack("<H",value))
        self._left = value
    @top.setter
    def top_setter(self,value):
        if not "top" in self._memlocs or not self._wrtbl:
            raise ValueError
        self._strm.seek(self._memlocs["top"])
        self._strm.write(struct.pack("<H",value))
        self._top = value
    @width.setter
    def width_setter(self,value):
        if not "width" in self._memlocs or not self._wrtbl:
            raise ValueError
        self._strm.seek(self._memlocs["width"])
        self._strm.write(struct.pack("<H",value))
        self._width = value
    @height.setter
    def height_setter(self,value):
        if not "height" in self._memlocs or not self._wrtbl:
            raise ValueError
        self._strm.seek(self._memlocs["height"])
        self._strm.write(struct.pack("<H",value))
        self._height = value

    def parse(self,strm,writeable):
        self._wrtbl = writeable
        self._origin = strm.tell()
        self._memlocs["left"] = self._origin
        self._memlocs["top"] = self._origin + 2
        self._memlocs["width"] = self._origin + 4
        self._memlocs["height"] = self._origin + 6
        self._left, self._top, self._width, self._height, pkd = struct.unpack("<HHHHB",strm.read(9))
        self._strm = strm
        if ((pkd>>7)&1) > 0:
            self._local_color_table = ColorTable()
            self._local_color_table.parse(pkd&0b111,strm,writeable)
        self._data = ImageData()
        self._data.parse(strm,writeable)

    def rebuild(self,strm):
        pkd = 0
        if self._local_color_table is not None:
            pkd |= 1<<7
            pkd |= (int(math.sqrt(self._local_color_table.color_num)-1)&0b111)
        strm.write(struct.pack("<HHHHB",self._left,self._top,self._width,self._height,pkd))
        if self._local_color_table is not None:
            self._local_color_table.rebuild(strm)
        self._data.rebuild(strm)

class GIFFile:
    def __init__(self):
        self._blocks = []
        self._header = None
        self._version = None
        self._vernum = None
        self._canvasW = 0
        self._canvasH = 0
        self._bkgCol = 0
        self._pixAspectRatio = 0
        self._memlocs = {}
        self._wrtbl = False
        self._stream = None
        self._global_color_table = None
        self._blocks = []
        self._data_off = 0
        self._data_end = 0

    @property
    def extensions(self):
        return list(filter(lambda x: type(x) is Extension,self._blocks))
    @property
    def images(self):
        return list(filter(lambda x: type(x) is Image, self._blocks))
    @property
    def global_color_table(self):
        return self._global_color_table
    @property
    def canvas_width(self):
        return self._canvasW
    @property
    def canvas_height(self):
        return self._canvasH
    @property
    def bkg_color_index(self):
        return self.bkgCol
    @property
    def pixel_aspect_ratio(self):
        return self.pix_aspect_ratio

    @bkg_color_index.setter
    def bkg_color_index_set(self,value):
        if not "bkgCol" in self._memlocs or not self._wrtbl:
            raise ValueError
        else:
            self._stream.seek(self._memlocs["bkgCol"])
            self._stream.write(struct.pack("<B",value))

    @pixel_aspect_ratio.setter
    def pix_aspect_ratio_set(self,value):
        if not "pixAspect" in self._memlocs or not self._wrtbl:
            raise ValueError
        else:
            self._stream.seek(self._memlocs["pixAspect"])
            self._stream.write(struct.pack("<B",value))

    @canvas_width.setter
    def canvas_width_set(self,value):
        if not "canvasW" in self._memlocs or not self._wrtbl:
            raise ValueError
        else:
            self._stream.seek(self._memlocs["canvasW"])
            self._stream.write(struct.pack("<H",value))

    @canvas_height.setter
    def canvas_height_set(self,value):
        if not "canvasH" in self._memlocs or not self._wrtbl:
            raise ValueError
        else:
            self._stream.seek(self._memlocs["canvasH"])
            self._stream.write(struct.pack("<H",value))

    def read_from_path(self,path):
        with open(path,"rb") as gffle:
            self.read_from_stream(gffle,False)
    
    def open_gif_file(self,path):
        fle = open(path,"r+b")
        self.read_from_stream(fle,True)
    def close_fle(self):
        self._stream.close()

    def recompile(self):
        fle = self._stream
        fle.seek(0)
        fle.truncate(0)
        fle.write(self._header)
        fle.write(self._version)
        pkd = 0
        if self._global_color_table is not None:
            pkd |= (1<<7)
            pkd |= (int(math.sqrt(self._global_color_table.color_num)-1)&0b111)
        fle.write(struct.pack("<HHBBB",self._canvasW,self._canvasH,pkd,self._bkgCol,self._pixAspectRatio))
        if self._global_color_table is not None:
            self._global_color_table.rebuild(fle)

        for blk in self._blocks:
            if type(blk) is Extension:
                fle.write(b'\x21')
                blk.rebuild(fle)
            if type(blk) is Image:
                fle.write(b'\x2C')
                blk.rebuild(fle)
        fle.write(b'\x3B')

    def read_from_stream(self,strm,writeable=False):
        self._wrtbl = writeable
        self._stream = strm
        
        self._header = strm.read(3)
        self._version = strm.read(3)
        self._vernum = struct.unpack("<H",self._version[:2])
        self._memlocs["canvasW"] = strm.tell()
        self._memlocs["canvasH"] = self._memlocs["canvasW"]+2
        self._memlocs["bkgCol"] = self._memlocs["canvasH"]+3
        self._memlocs["pixAspect"] = self._memlocs["bkgCol"]+1
        self._canvasW, self._canvasH, packed_fld, self._bkgCol, self._pixAspectRatio = struct.unpack("<HHBBB",strm.read(7))
        if ((packed_fld>>7)&1) > 0:
            self._global_color_table = ColorTable()
            self._global_color_table.parse(packed_fld&0b111,strm,writeable)
        

        self._data_off = strm.tell()
        while True:
            terminator = strm.read(1)
            if len(terminator) == 0:
                break
            elif terminator[0] == 0x21:
                ext = Extension()
                ext.parse(strm,writeable)
                self._blocks.append(ext)
            elif terminator[0] == 0x2C:
                img = Image()
                img.parse(strm,writeable)
                self._blocks.append(img)
        self._data_end = strm.tell()

class GIFComposite:
    def __init__(self):
        self._blocks = []
        self._data_table = []
    
    def from_gif(self,gif):
        ext_index = 0
        img_index = 0

        if gif.global_color_table is not None:
            self._data_table.append((0,0,0xCC,0,gif.global_color_table))

        for ext in gif.extensions:
            self._data_table.append((0,0,0xEE,ext_index,ext))
            ext_index += 1
        for img in gif.images:
            self._data_table.append((0,0,0x11,img_index,img))
            img_index += 1

    def create(self,path):
        with open(path,"wb") as fle:
            fle.write(struct.pack("<I",len(self._data_table)))
            for data_entry in self._data_table:
                fle.write(b'\x00\x00\x00\x00\x33\x33\x33\x33\x11\x22\x22')
            for i in range(len(self._data_table)):
                a,b, typ, idx, data = self._data_table[i]
                origin = fle.tell()
                data.rebuild(fle)
                end = fle.tell()
                self._data_table[i] = (origin,end-origin,typ,idx,data)
            fle.seek(4)
            for data_entry in self._data_table:
                fle.write(struct.pack("<IIBH",data_entry[0],data_entry[1],data_entry[2],data_entry[3]))
