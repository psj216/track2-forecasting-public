"""## Executive summary (read this first)
Separate existing full text forecasts from their pure center translation.
"""
import numpy as np
def text_shift(text,numeric):return np.median(text,axis=0)-np.median(numeric,axis=0)
def standardized_shift(text,numeric):return text_shift(text,numeric)/np.maximum(np.std(numeric,axis=0,ddof=0),1e-12)
def location_only(text,numeric):return numeric+text_shift(text,numeric)
