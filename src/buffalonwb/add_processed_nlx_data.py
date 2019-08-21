# add processed nlx data
import h5py
from pynwb.ecephys import ElectricalSeries
import numpy as np
import os
import pynwb
from hdmf.data_utils import DataChunkIterator
from exceptions import InconsistentInputException, UnexpectedInputException


def add_lfp(nwbfile, lfp_file_name, electrode_table_region, num_electrodes, proc_module, iterator_flag):
    if iterator_flag:
        print("LFP adding via data chunk iterator")
        lfp, lfp_timestamps, lfp_resolution = get_lfp_data(1, lfp_file_name)
        lfp_data = DataChunkIterator(data=lfp_generator(lfp_file_name,num_electrodes), iter_axis=1)
    else:
        lfp_data, lfp_timestamps, lfp_resolution = get_lfp_data(num_electrodes, lfp_file_name)

    # time x 120
    # add the lfp metadata - some in the lab metadata and some in the electrical series
    lfp_es = ElectricalSeries('LFP_data',
                              lfp_data,
                              electrode_table_region,
                              timestamps=np.squeeze(lfp_timestamps),
                              resolution=lfp_resolution,
                              comments="LFP",
                              description="LFP")

    # put LFP data in ecephys
    # what is the most efficient/pythonic way to do this?

    nwbfile.add_acquisition(pynwb.ecephys.LFP(electrical_series=lfp_es, name='LFP'))
    proc_module.add_data_interface(pynwb.ecephys.LFP(electrical_series=lfp_es, name='LFP'))


# FUNCTIONS FOR PROCESSED DATA
# no input checking for now
# add back input checking soon #FIXTHIS

# process nlx mat file into dictonary
# needs: data, timestamps, resolution, time, rate
def MH_process_nlx_mat_file(nlx_file_name):
    # for some reason files 7-9 don't exist
    # as a stop gap we'll skip them
    # FIXTHIS
    if os.path.exists(nlx_file_name):
        nlx_file = h5py.File(nlx_file_name, 'r')
        print(nlx_file_name)
    else:
        msg = 'skipped ' + str(nlx_file_name + ', returning empty dict')
        print(msg)
        return dict()

    # raw sampling frequency
    Fs = check_get_scalar(nlx_file['Fs'][()])

    # first timestamp in raw data
    first_ts = check_get_scalar(nlx_file['firstts'][()])

    # lfp sampling frequency, should be same as value in params.lfpfq
    lfp_Fs = check_get_scalar(nlx_file['lfpfq'][()])

    # lfp values -- units?
    lfp = nlx_file['lfp'][()]

    # lfp timestamps, num columns should match num columns of lfp
    lfp_ts = nlx_file['lfpts'][()]
    lfp_ts = nlx_file['lfpts'][()]

    # check lfp_ts, then keep only starting time (first_lfp_ts) and rate (lfp_Fs)
    diff_lfp_ts = np.diff(lfp_ts)
    first_lfp_ts = lfp_ts[0][0]

    # get spike times
    spk_ts = nlx_file['spkts'][()]

    # get spike waveforms
    spk_wfs = nlx_file['spkwv'][()]

    # get preprocessing parameters
    n_std = check_get_scalar(nlx_file['params']['n_std'])  # standard deviations used for thresholding
    rawspk = check_get_scalar(nlx_file['params']['rawspk'])  # ??? 0 in sample file
    resamp = check_get_scalar(nlx_file['params']['resamp'])  # ??? 1 in sample file
    saveupsamp = check_get_scalar(nlx_file['params']['saveupsamp'])  # ??? 0 in sample file
    spkfq = check_get_scalar(nlx_file['params']['spkfq'])  # ??? 400 in sample file
    # MH- ??? what is up with this #FIXTHIS

    # i'm guessing spkbuff specifies num samples before threshold crossing and num samples after threshold
    spk_buff = nlx_file['params']['spkbuff'][()]
    spk_buff = spk_buff.transpose()[0].tolist()

    # variables of interest
    dict_vars = {'Fs', 'first_ts', 'lfp_Fs', 'lfp', 'lfp_ts', 'first_lfp_ts', 'spk_ts', 'spk_wfs', 'n_std', 'rawspk',
                 'resamp', 'saveupsamp', 'spkfq', 'spk_buff'}

    # make a dictionary
    file_dict = dict()
    for i in dict_vars:
        file_dict[i] = locals()[i]

    # DELETE NLX FILE TO CLEAN MEMORY
    del nlx_file

    return file_dict


def check_get_scalar(v):
    if v.shape != (1, 1):
        raise UnexpectedInputException()
    if v[0].shape != (1,):
        raise UnexpectedInputException()
    return v[0][0]


def get_lfp_data(num_electrodes, lfp_file):
    processed = MH_process_nlx_mat_file(''.join([lfp_file.split("_FILENUM_")[0], str(1), lfp_file.split("_FILENUM_")[1]]))
    num_ts = max(processed["lfp_ts"].shape)
    lfp = np.full((num_electrodes, num_ts), np.nan)
    ts = processed["lfp_ts"]
    fs = processed["Fs"]
    # check if ts are all the same
    for f in range(1, num_electrodes):
        file_name = ''.join([lfp_file.split("_FILENUM_")[0], str(f), lfp_file.split("_FILENUM_")[1]])
        processed_file = MH_process_nlx_mat_file(file_name)
        if processed_file:
            lfp[f, :] = processed_file["lfp"]
    return lfp, ts, fs

def lfp_generator(lfp_file,num_electrodes):
    # generate lfp data chunks
    for x in range(1, num_electrodes + 1):
        file_name = ''.join([lfp_file.split("_FILENUM_")[0], str(x), lfp_file.split("_FILENUM_")[1]])
        processed_data = MH_process_nlx_mat_file(file_name)
        lfp_data = processed_data["lfp"]
        del processed_data
        yield lfp_data
    return