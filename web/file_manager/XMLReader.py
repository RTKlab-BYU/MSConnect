import xml.sax
from collections import deque
from datetime import datetime


class CustomContentHandler(xml.sax.handler.ContentHandler):
    """
    Custom content handler for XML parsing.
    """
    def __init__(self):
        self.model = None
        self.SN = None
        self.acquisition_time = None
        self.ms1_rt = []
        self.ms1_basemzintensity = []
        self.ms1_ticintensity = []
        self.ms2_rt = []
        self.ms2_injectiontime = []
        self.current_ms_level = None
        self.rolling_list = self.create_rolling_list(20)
        # create a 20 tag list to track histry

    def create_rolling_list(self, max_length):
        rolling_list = deque(maxlen=max_length)
        return rolling_list

    def add_item(self, item):
        self.rolling_list.append(item)

    def startElement(self, name, attrs):
        # get MS level
        if name == "cvParam" and attrs["name"] == "ms level":
            self.current_ms_level = attrs["value"]
        if self.current_ms_level == "1":
            # get MS1 RT, base peak intensity, TIC
            if name == "cvParam" and attrs["name"] == "scan start time":
                self.ms1_rt.append(float(attrs["value"]))
            elif name == "cvParam" and attrs["name"] == "base peak intensity":
                self.ms1_basemzintensity.append(float(attrs["value"]))
            elif name == "cvParam" and attrs["name"] == "total ion current":
                self.ms1_ticintensity.append(float(attrs["value"]))

        elif self.current_ms_level == "2":
            # get MS2 RT, injection time
            if name == "cvParam" and attrs["name"] == "scan start time":
                self.ms2_rt.append(float(attrs["value"]))
            elif name == "cvParam" and attrs["name"] == "ion injection time":
                self.ms2_injectiontime.append(float(attrs["value"]))
        # get acquisition time
        if name == "run" and attrs["startTimeStamp"]:
            self.acquisition_time = datetime.strptime(attrs[
                "startTimeStamp"], "%Y-%m-%dT%H:%M:%SZ")
        if name == "cvParam" and self.rolling_list[
                -1] == "referenceableParamGroup":
            self.model = attrs["name"]

        # get instrument serial number and model
        # for Thermo systems
        if name == "cvParam" and attrs["name"] == "instrument serial number":
            self.SN = attrs["value"]

        # for Bruker systems #need to be confirmed after the change search mode
        if name == "cvParam" and self.rolling_list[
                -1] == "instrumentConfiguration":
            self.SN = attrs["value"]

        # add the tag to the rolling list
        self.add_item(name)

    def endElement(self, name):
        # when search at the end of a tag, not used here
        pass

    def characters(self, content):
        """Get characters between opening and closing tags.
        when search at the content of a tag, no data in mzML
        file is in the content"""
        # if self.ms1_rt is not None:
        #    data = content
        pass


if __name__ == '__main__':

    handler = CustomContentHandler()
    xml.sax.parse("./Cell1097_QC1_Q9i91W3.mzML", handler)
    print(handler.model, handler.SN, handler.acquisition_time)
    print(handler.ms1_rt,
          handler.ms1_basemzintensity,
          handler.ms1_ticintensity)
    # self.file_year, self.file_month, self.file_day = \
    #             handler.acquisition_time.year, \
    #             handler.acquisition_time.month, \
    #             handler.acquisition_time.day
