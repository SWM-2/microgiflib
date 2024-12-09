import struct

class ColorTable:
    def __init__(self):
        self._colors = []
        self._wrtbl = False
        self._entry_count = 0
        self._origin = 0
        self._strm = None

    def parse(self,size_num,strm,writeable):
        self._wrtbl = writeable
        self._entry_count = 2**(1+size_num)
        self._origin = strm.tell()
        self._strm = strm
        for i in range(self._entry_count):
            r,g,b = strm.read(3)
            self._colors.append((int(r),int(g),int(b)))

    def rebuild(self,strm):
        for color in self._colors:
            strm.write(struct.pack("<BBB",color[0],color[1],color[2]))
    
    def get_color(self,index):
        if index < len(self._colors):
            return self._colors[index]
        else:
            raise IndexError
    def set_color(self,index,value):
        if not self._wrtbl:
            raise ValueError
        if index < len(self._colors):
            self._strm.seek(self._origin + (index*3))
            self._strm.write(struct.pack("<BBB",value[0],value[1],value[2]))
        else:
            raise IndexError
    @property
    def color_num(self):
        return self._entry_count