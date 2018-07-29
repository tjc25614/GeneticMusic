# Genetic Algorithm for identifying music notes in a wave file
# Tom Conroy, 7/28/2018

import wave
import sys
import binascii
import random
import math
import struct
import argparse

# Note and their frequencies (A440 tuning)
frequencies = { 'C1':   32.7,
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
                'B6':   1975.53}

# Compares samples of two lists of samples and produces a fitness score
def fitness(test_audio, answer_audio, byte_depth):
    if len(test_audio) != len(answer_audio):
        print 'Error: test audio and answer audio not the same length'
        sys.exit()
    fitness_score = 0
    correct_sample = ''
    test_sample = ''
    for test_val,correct_val in zip(test_audio,answer_audio):
        correct_sample += chr(correct_val)
        test_sample += chr(test_val)
        if len(correct_sample) == byte_depth:
            if byte_depth == 2:
                fitness_score += abs(struct.unpack('h', test_sample)[0] - struct.unpack('h', correct_sample)[0])
            else:
                fitness_score += abs(ord(test_sample) - ord(correct_sample))
            correct_sample = ''
            test_sample = ''
    return fitness_score

# Creates chromosomes, genes being:
#   frequencies
#   phase
def GenerateChromosome(n_samples, sample_rate, bpm, division):
    min_time = 60.0 / (bpm * division)
    total_time = float(n_samples) / sample_rate
    number_of_smallest_divisions = total_time / min_time
    chromosome = []
    for i in range(int(number_of_smallest_divisions)):
        freq = random.choice(frequencies.values())
        phase = (2 * math.pi * random.random()) - math.pi
        chromosome.append((freq,phase))
    return chromosome

# convert chromosomes to audio data samples
def generate_random_audio(chromosome, n_samples, sample_rate, byte_depth, n_channels, bpm, division):
    # time in seconds of each division
    min_time = 60.0 / (bpm * division)
    total_time = float(n_samples) / sample_rate
    number_of_smallest_divisions = total_time / min_time
    samples_per_division = n_samples / number_of_smallest_divisions
    
    chromo = []
    audio_data = []
    for gene in chromosome:
        freq = gene[0]
        phase = gene[1]
        for s in range(int(samples_per_division)):
            s_time = (min_time * s) / samples_per_division
            sample_val = 0
            if byte_depth == 1:
                sample_val = int(127 * (math.sin((2*math.pi*freq*s_time) + phase) + (0.5 * math.sin((4*math.pi*freq*s_time) + phase)) + (0.25 * math.sin((6*math.pi*freq*s_time) + phase))) / 1.75) + 128
                if n_channels == 1:
                    audio_data.append(sample_val)
                else:
                    audio_data.append(sample_val)
                    audio_data.append(sample_val)
            else:
                sample_val = int(32767 * (math.sin((2*math.pi*freq*s_time) + phase) + (0.5 * math.sin((4*math.pi*freq*s_time) + phase)) + (0.25 * math.sin((6*math.pi*freq*s_time) + phase))) / 1.75)
                val = struct.pack('h', sample_val)
                if n_channels == 1:
                    audio_data.append(ord(val[0]))
                    audio_data.append(ord(val[1]))
                else:
                    audio_data.append(ord(val[0]))
                    audio_data.append(ord(val[1]))
                    audio_data.append(ord(val[0]))
                    audio_data.append(ord(val[1]))
    missing = (n_samples*byte_depth*n_channels) - len(audio_data)
    for i in range(missing):
        audio_data.append(128)
    return audio_data

# take audio data and convert it to the format the wave library likes
def ConvertBackToSamples(audio_data):
    return ''.join(chr(b) for b in audio_data)
    
# randomly change <mutation rate> genes
def MutateChromosome(chromosome,mutation_rate):
    new_chromosome = []
    for gene in chromosome:
        freq =  gene[0]
        phase = gene[1]
        if random.random() < mutation_rate:
            freq = random.choice(frequencies.values())
        if random.random() < mutation_rate:
            phase = (2 * math.pi * random.random()) - math.pi
        new_chromosome.append((freq, phase))
    return new_chromosome
        
# take two chromosomes, make a mix of the two
def CrossoverChromosomes(chromosome1,chromosome2):
    new_chromosome = []
    for gene1,gene2 in zip(chromosome1, chromosome2):
        if random.random() < 0.5:
            freq = gene1[0]
        else:
            freq = gene2[0]
        if random.random() < 0.5:
            phase = gene1[1]
        else:
            phase = gene2[1]
        new_chromosome.append((freq,phase))
    return new_chromosome

# Use argparse to create command line options
def ParseArguments():
    parser = argparse.ArgumentParser(description='Feed it a wave file of some music. It will genetically figure out what note (singular) is playing')
    parser.add_argument('file', help='The wave file of music')
    parser.add_argument('bpm', type=int, help='The number of beats per minute of the music')
    parser.add_argument('divisions', type=int, help='The largest number of divisions of a beat, e.g. if the music contains 16th notes, they (usually) divide the beat by 4')
    parser.add_argument('--initial-population', type=int, help='The size of the initial population (default 30)')
    parser.add_argument('--generations', type=int, help='The number of generations to complete')
    parser.add_argument('--mutation-rate', help='How often genes change. Give as a decimal less than 1, e.g. 0.2')
    argNamespace = parser.parse_args()
    args = vars(argNamespace)
    if args['initial_population'] is None:
        args['initial_population'] = 30
    if args['generations'] is None:
        args['generations'] = 20
    if args['mutation_rate'] is None:
        args['mutation_rate'] = 0.25
    return args
    
def RunGenerations():
    args = ParseArguments()
    audio_file_name = args['file']
    bpm = args['bpm']
    divisions = args['divisions']
    audio_file = wave.open(audio_file_name, 'r')
    n_frames = audio_file.getnframes()
    byte_depth = audio_file.getsampwidth()
    n_channels = audio_file.getnchannels()
    print 'Audio file has %s samples' % n_frames
    print 'Number of channels: %d' % n_channels
    print 'Sample width (bytes): %d' % byte_depth
    audio_data_string = audio_file.readframes(n_frames)
    framerate = audio_file.getframerate()
    
    audio_data = []
    for sample in audio_data_string:
        audio_data.append(ord(sample))
    print 'Length of audio data: %d' % len(audio_data)
    chromosomes = []
    test_datas = []
    fitnesses = []
    # generate initial population
    for i in range(args['initial_population']): # initial population size
        chromosome = GenerateChromosome(n_frames, framerate, bpm, divisions)
        
        test_data = generate_random_audio(chromosome, n_frames, framerate, byte_depth, n_channels, bpm, divisions)
        chromosomes.append(chromosome)
        test_datas.append(test_data)
        fitnesses.append(fitness(test_data, audio_data, byte_depth))
    
    # run populations
    new_chromosomes = []
    new_test_datas = []
    new_fitnesses = []
    for gen in range(args['generations']): # number of populations
        print 'Running Generation #%d' % (gen+1)
        sorted_fitnesses = sorted(fitnesses)
        sorted_chromosomes = []
        for f in sorted_fitnesses:
            c_index = fitnesses.index(f)
            sorted_chromosomes.append(chromosomes[c_index])
        for c in sorted_chromosomes[:len(sorted_chromosomes)//6]:
            chromosome = c
            new_chromosomes.append(chromosome)
            
            # mutate a couple
            for i in range(2):
                chromosome = MutateChromosome(c, args['mutation_rate'])
                new_chromosomes.append(chromosome)
                
            # cross a couple over with it
            for i in range(2):
                chromosome = CrossoverChromosomes(c, random.choice(sorted_chromosomes))
                new_chromosomes.append(chromosome)
                
            # pick a random one (lucky survivor)
            chromosome = random.choice(sorted_chromosomes)
            new_chromosomes.append(chromosome)
            
        for c in new_chromosomes:
            test_data = generate_random_audio(c, n_frames, framerate, byte_depth, n_channels, bpm, divisions)
            new_test_datas.append(test_data)
            new_fitnesses.append(fitness(test_data, audio_data, byte_depth))
        
        chromosomes = new_chromosomes
        test_datas = new_test_datas
        fitnesses = new_fitnesses
        new_chromosomes = []
        new_test_datas = []
        new_fitnesses = []
        print 'Min Fitness: %d' % min(fitnesses)
    
    c = chromosomes[0]
    print 'Done!'
    print 'Notes',
    for gene in c:
        print frequencies.keys()[frequencies.values().index(gene[0])],
    print ''
    export_audio = ConvertBackToSamples(test_datas[0])
    export_wave_file = wave.open('export.wav', 'w')
    export_wave_file.setnchannels(n_channels)
    export_wave_file.setsampwidth(byte_depth)
    export_wave_file.setframerate(framerate)
    export_wave_file.writeframesraw(export_audio)
    
if __name__ == "__main__":
    RunGenerations()