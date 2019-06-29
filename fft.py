# FFT method for dentifying music notes in a wave file
# Tom Conroy, 6/16/2019

import wave
import sys
import binascii
import math
import struct
import argparse
import numpy as np
from collections import OrderedDict
# Note and their frequencies (A440 tuning)
frequencies = OrderedDict({ 'C1':   32.7,
                'C#1':  34.65,
                'D1':   36.71,
                'D#1':  38.89,
                'E1':   41.2,
                'F1':   43.65,
                'F#1':  46.25,
                'G1':   49.0,
                'G#1':  51.91,
                'A1':   55.0,
                'A#1':  58.27,
                'B1':   61.74,
                'C2':   65.41,
                'C#2':  69.3,
                'D2':   73.42,
                'D#2':  77.78,
                'E2':   82.41,
                'F2':   87.31,
                'F#2':  92.5,
                'G2':   98.0,
                'G#2':  103.83,
                'A2':   110.0,
                'A#2':  116.54,
                'B2':   123.47,
                'C3':   130.81,
                'C#3':  138.59,
                'D3':   146.83,
                'D#3':  155.56,
                'E3':   164.81,
                'F3':   174.61,
                'F#3':  185.0,
                'G3':   196.0,
                'G#3':  207.65,
                'A3':   220.0,
                'A#3':  223.08,
                'B3':   246.94,
                'C4':   261.63,
                'C#4':  277.18,
                'D4':   293.66,
                'D#4':  311.13,
                'E4':   329.23,
                'F4':   349.23,
                'F#4':  369.99,
                'G4':   392.0,
                'G#4':  415.3,
                'A4':   440.0,
                'A#4':  466.16,
                'B4':   493.88,
                'C5':   525.25,
                'C#5':  554.37,
                'D5':   587.33,
                'D#5':  622.25,
                'E5':   659.25,
                'F5':   698.46,
                'F#5':  739.99,
                'G5':   783.99,
                'G#5':  830.61,
                'A5':   880.0,
                'A#5':  932.33,
                'B5':   987.77,
                'C6':   1046.5,
                'C#6':  1108.73,
                'D6':   1174.66,
                'D#6':  1244.51,
                'E6':   1318.51,
                'F6':   1396.51,
                'F#6':  1479.98,
                'G6':   1567.98,
                'G#6':  1661.22,
                'A6':   1760.00,
                'A#6':  1864.66,
                'B6':   1975.53,
                'C7':   2093.00,
                'C#7':  2217.46,
                'D7':   2349.32,
                'D#7':  2489.02,
                'E7':   2637.02,
                'F7':   2793.83,
                'F#7':  2959.96,
                'G7':   3135.96,
                'G#7':  3322.44,
                'A7':   3520.00,
                'A#7':  3729.31,
                'B7':   3951.07})

# finds n highest amplitude frequencies
def find_maxima(fft_result, division_time, n=5):
    sorted_fft = np.sort(fft_result[:len(fft_result) // 2])
    notes = []
    for note in sorted_fft[-n:]:
        freq = np.where(fft_result ==  note)[0].tolist()[0] / division_time
        notes.append(freq)
    return notes

# convert notes to audio data samples
def generate_audio(letter_notes, n_samples, sample_rate, byte_depth, n_channels, bpm, division):
    # time in seconds of each division
    min_time = 60.0 / (bpm * division)
    total_time = float(n_samples) / sample_rate
    number_of_smallest_divisions = total_time / min_time
    samples_per_division = n_samples / number_of_smallest_divisions
    
    frame_data = []
    s_time = 0
    for current_letter_notes in letter_notes:
        for s in range(int(samples_per_division)):
            s_time += min_time / samples_per_division
            sample_val = 0
            amplitude = 0
            for letter in current_letter_notes:
                note = frequencies[letter]
                amplitude += 1
                if byte_depth == 1:
                    sample_val += int(127 * math.sin(2*math.pi*note*s_time)) + 128
                else:
                    sample_val += int(32767 * math.sin(2*math.pi*note*s_time))
            sample_val = sample_val // amplitude
            if byte_depth == 1:
                val = bytes([sample_val])
            else:
                val = struct.pack('<h', sample_val)
            if n_channels == 1:
                frame_data.append(val)
            else:
                frame_data.append(val)
                frame_data.append(val)
    audio_data = b''.join(b for b in frame_data)
    missing = (n_samples*byte_depth*n_channels) - len(audio_data)
    audio_data += missing*bytes([128])
    return audio_data

# Use argparse to create command line options
def ParseArguments():
    parser = argparse.ArgumentParser(description='Feed it a wave file of some music. It will genetically figure out what note (singular) is playing')
    parser.add_argument('file', help='The wave file of music')
    parser.add_argument('bpm', type=int, help='The number of beats per minute of the music')
    parser.add_argument('divisions', type=int, help='The largest number of divisions of a beat, e.g. if the music contains 16th notes, they (usually) divide the beat by 4')
    parser.add_argument('-v', '--voices', type=int, help='The number of voices to pull from the audio')
    parser.add_argument('-o', '--output-file', help='File which to output generated audio')
    argNamespace = parser.parse_args()
    args = vars(argNamespace)
    return args
    
def RunAnalysis():
    args = ParseArguments()
    audio_file_name = args['file']
    bpm = args['bpm']
    divisions = args['divisions']
    voices = 5
    if 'voices' in args.keys():
        if args['voices'] is not None:
            voices = args['voices']
    audio_file = wave.open(audio_file_name, 'rb')
    n_frames = audio_file.getnframes()
    byte_depth = audio_file.getsampwidth()
    n_channels = audio_file.getnchannels()

    print('Running note recognition on file: %s' % audio_file_name)
    print('Audio file has %s frames' % n_frames)
    print('Number of channels: %d' % n_channels)
    print('Sample width (bytes): %d' % byte_depth)
    if n_channels == 2:
        left_audio_samples = []
        right_audio_samples = []
        for i in range(n_frames):
            frame = audio_file.readframes(1)
            if byte_depth == 2:
                left_sample = int.from_bytes(frame[:2], byteorder="little", signed=True) / 32767
                right_sample = int.from_bytes(frame[2:], byteorder="little", signed=True) / 32767
                
                left_audio_samples.append(left_sample)
                right_audio_samples.append(right_sample)
            else:
                left_sample = ord(frame[0])
                right_sample = ord(frame[1])
                
                left_audio_samples.append(left_sample)
                right_audio_samples.append(right_sample)
    else:
        audio_samples = []
        for i in range(n_frames):
            frame = audio_file.readframes(1)
            if byte_depth == 2:
                sample = int.from_bytes(frame, byteorder="little", signed=True) / 32767
                audio_samples.append(sample)
            else:
                sample = ord(frame[0])
                audio_samples.append(sample)

    framerate = audio_file.getframerate()
    print("Sample rate of audio: %d" % framerate)
    audio_file.close()

    frametime = 1 / framerate
    division_time = 1 / (bpm * divisions / 60)
    frames_per_division = int(framerate * division_time)
    notes = []
    for i in range(n_frames // frames_per_division):
        fft_result = np.abs(np.fft.fft(left_audio_samples[i*frames_per_division:(i+1)*frames_per_division]))
        current_notes = find_maxima(fft_result, division_time, voices)
        notes.append(current_notes)

    letter_notes = []
    print('Notes:', end=' ')
    for current_notes in notes:
        current_letter_notes = []
        for note in current_notes:
            diff = 10000
            letter = 'C1'
            for pitch in frequencies.keys():
                if abs(frequencies[pitch] - note) > diff:
                    break
                else:
                    letter = pitch
                    diff = abs(frequencies[pitch] - note)
            current_letter_notes.append(letter)
        letter_notes.append(current_letter_notes)
        print(current_letter_notes, end=' ')
    print('')

    print("Generating audio file...")
    final_audio = generate_audio(letter_notes, n_samples=n_frames, sample_rate=framerate, byte_depth=byte_depth, n_channels=n_channels, bpm=bpm, division=divisions)
    
    print('Done!')
    
    of = 'export.wav'
    if 'output_file' in args.keys():
        of = args['output_file']
    export_wave_file = wave.open(of, 'wb')
    export_wave_file.setnchannels(n_channels)
    export_wave_file.setsampwidth(byte_depth)
    export_wave_file.setframerate(framerate)
    export_wave_file.writeframesraw(final_audio)
    export_wave_file.close()

if __name__ == "__main__":
    RunAnalysis()