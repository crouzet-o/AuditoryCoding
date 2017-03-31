#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 30 17:32:25 2017

@author: Rachid and Kimia
"""


from scikits.audiolab import Sndfile, play
import numpy as np
import matplotlib.pyplot as plt

import numpy as np
from sklearn.decomposition import SparseCoder

def gammatone_function(resolution, fc, center, fs=16000, n=4,
                       b=1.019):
    t = np.linspace(0, resolution-(center+1), resolution-center)/fs
    g = np.zeros((resolution,))
    g[center:] = t**(n-1) * np.exp(-2*np.pi*b*erb(fc)*t)*np.cos(2*np.pi*fc*t)
    return g

def gammatone_matrix(b, fc, resolution, step, fs=16000, n=4, threshold=5):
    """Dictionary of gammatone functions"""
    centers = np.arange(0, resolution - step, step)
    D = []
    for i, center in enumerate(centers):
        t = np.linspace(0, resolution-(center+1), resolution-center)/fs
        env = t**(n-1) * np.exp(-2*np.pi*b*erb(fc)*t)
        if env[-1]/max(env) < threshold:
            D.append(gammatone_function(resolution, fc, center, b=b, n=n))
    D = np.asarray(D)
    D /= np.sqrt(np.sum(D ** 2, axis=1))[:, np.newaxis]
    freq_c = np.array(fc*np.ones(D.shape[0]))
    return D,freq_c,centers

def erb(f):
    return 24.7+0.108*f

def erb_space(low_freq, high_freq, num_channels = 1, EarQ = 9.26449, minBW = 24.7, order = 1):
    return -(EarQ*minBW) + np.exp(np.arange(1,num_channels+1)*(-np.log(high_freq + EarQ*minBW) + np.log(low_freq + EarQ*minBW))/num_channels) * (high_freq + EarQ*minBW)

if __name__ == '__main__':
    from scikits.talkbox import segment_axis
    resolution = 5000
    step = 6
    b = 1.019
    n_channels = 8
    overlap = 80
    
    # Compute a multiscale dictionary
    
    D_multi = np.r_[tuple(gammatone_matrix(b, fc, resolution, step) for
                          fc in erb_space(150, 8000, n_channels))]

    # Load test signal
    filename = 'data/fsew/fsew0_001.wav'
    f = Sndfile(filename, 'r')
    nf = f.nframes
    fs = f.samplerate
    y = f.read_frames(nf)
    y = y / 2.0**15
    Y = segment_axis(y, resolution, overlap=overlap, end='pad')
    Y = np.hanning(resolution) * Y

    # segments should be windowed and overlap
    
    coder = SparseCoder(dictionary=D_multi, transform_n_nonzero_coefs=None, transform_alpha=1., transform_algorithm='omp')
    X = coder.transform(Y)
    density = len(np.flatnonzero(X))
    out= np.zeros(int((np.ceil(len(y)/resolution)+1)*resolution))
    for k in range(0, len(X)):
        idx = range(k*(resolution-overlap),k*(resolution-overlap) + resolution)
        out[idx] += np.dot(X[k], D_multi)
    squared_error = np.sum((y - out[0:len(y)]) ** 2)
    play(y*2.0**15,fs=16000)
    play(out*2.0**15,fs=16000)
#    wavfile.write('reconst_%d_%d.wav'%(resolution,overlap), fs, np.asarray(out, dtype=np.float32))