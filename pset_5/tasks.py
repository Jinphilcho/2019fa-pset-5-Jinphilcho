from csci_utils.luigi.dask.target import *
from csci_utils.luigi.task import *
from luigi import Task, ExternalTask, BoolParameter

class YelpReviews(ExternalTask):


    def output(self):
        AWS_ROOT = '/Users/Jinphil/PycharmProjects/2019fa-pset-5-Jinphilcho/pset_5/data/'
        c = CSVTarget(AWS_ROOT)
        return c._read(path=AWS_ROOT+'*.csv', storage_options={'requester_pays':True}, assume_missing=True)


class CleanedReviews(Task):
    subset = BoolParameter(default=True)

    # Output should be a local ParquetTarget in ./data, ideally a salted output,
    # and with the subset parameter either reflected via salted output or
    # as part of the directory structure

    requires = Requires()
    reviews = Requirement(YelpReviews).__module__

    output = TargetOutput(file_pattern='data/', target_class=ParquetTarget, glob='*.parquet')

    def run(self):

        numcols = ["funny", "cool", "useful", "stars"]
        strcols = ['review_id', 'user_id', 'business_id', 'text']
        dsk = YelpReviews.output(self)
        dsk[numcols] = dsk[numcols].astype("float64")
        dsk = dsk.fillna(0)
        dsk['date'] = dsk['date'].astype('datetime64')
        dsk = dsk[dsk.review_id.apply(lambda x: len(str(x)) == 22)]

        #dsk = dsk.set_index(dsk.review_id)
        dsk[numcols] = dsk[numcols].astype("int64")

        if self.subset:
            dsk = dsk.get_partition(0)

        dsk[strcols] = dsk[strcols].astype("str")

        self.output().write_dask(collection=dsk, compression='gzip')