from shared import Position,FileReader
import pandas as pd
import logging
import numpy as np


class ChiPSeqReader(FileReader): #Class proccess files with ChipSeq peaks
    def __init__(self,fname):
        self.data = None
        super(ChiPSeqReader,self).__init__(fname)

    def read_file(self): # store CTCF peaks as sorted pandas dataframe
        logging.log(msg="Reading CTCF file"+self.fname, level=logging.INFO)

        # set random temporary labels
        Nfields = len(open(self.fname).readline().strip().split())
        names = list(map(str,list(range(Nfields))))
        data = pd.read_csv(self.fname,sep="\t",header=None,names=names)

        # subset and rename
        data = data.iloc[:,0:3]
        data.rename(columns={"0":"chr","1":"start","2":"end"},inplace=True)

        #check duplicats
        duplicated = data.duplicated(subset = ["chr","start","end"])
        if sum(duplicated) > 0:
            logging.warning("Duplicates by genomic positions found in file "+self.fname) #TODO check why this happens
        del duplicated

        #get peak mids
        data["mids"] = (data["start"] + data["end"]) / 2

        #convert to chr-dict
        chr_data = dict([(chr,data[data["chr"]==chr]) \
                         for chr in pd.unique(data["chr"])])
        del data

        logging.warning(
            msg="Filling orientation and peak strength with mock values!") #TODO fill with real data

        for data in chr_data.values():
            data.sort_values(by=["chr","start"],inplace=True)
            data["orientation"] = [1]*len(data)
            data["strength"] = [1]*len(data)

        #save
        self.chr_data = chr_data

    def get_interval(self,interval): #return all peaks intersecting interval as pd.dataframen
        try:
            self.chr_data
        except:
            logging.error("Please read data first")
            return None

        if not interval.chr in self.chr_data:
            logging.error("Chromosome ",interval.chr,"not found in keys")
            return pd.DataFrame()

        left = np.searchsorted(self.chr_data[interval.chr]["mids"].values,interval.start,"left")
        right = np.searchsorted(self.chr_data[interval.chr]["mids"].values,interval.end,"right")
        assert left <= right
        return self.chr_data[interval.chr].iloc[min(len(self.chr_data[interval.chr])-1,left):max(0,right),:]

    def get_binned_interval(self,interval,binsize,extend=True): #return all peaks intersecting interval as list
                                                            #list len = interval len / bindsize
                                                            #if extend = True last bin is extended over interval's end
        try:
            self.chr_data
        except:
            logging.error("Please read data first")
            return None

        if not interval.chr in self.chr_data:
            logging.error("Chromosome ",interval.chr,"not found in keys")
            return pd.DataFrame()

        left_array = np.arange(interval.start,interval.end-1,binsize)
        right_array = left_array + binsize

        if (right_array[-1] >= interval.end) and (not extend):
            right_array[-1] = right_array.end+1

        left_ids = np.searchsorted(self.chr_data[interval.chr]["mids"].values,left_array,"left")
        right_ids = np.searchsorted(self.chr_data[interval.chr]["mids"].values,right_array,"right")

        result_strength = [0]*len(left_ids)

        for ind,(left,right) in enumerate(zip(left_ids,right_ids)):
            left = min(len(self.chr_data[interval.chr])-1,left)
            right = max(0,right)
            assert left <= right
            if left != right:
                result_strength[ind] = self.chr_data[interval.chr].strength.iloc[left:right].sum()
        return result_strength

