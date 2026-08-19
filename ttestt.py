import sounddevice as sd

sd.rec(16000,samplerate=44100,channels = 1,dtype = 'int16',device = 2)
sd.wait()