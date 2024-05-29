from __future__ import unicode_literals
import spacy

import numpy as np
import time
from scipy.interpolate import interp1d
from scipy import spatial
import math
from datetime import datetime
import multiprocessing
from multiprocessing import Process
import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QSlider, QLineEdit, QLabel, QHBoxLayout, QVBoxLayout, QWidget

# which source to base the punctuation on
template = []
s1 = []
s2 = []
nlp = None
blend_value = 100
blur_value = 5
resize_value = 25
generated_text = ""

def initialise():
    nlp = spacy.load('en_core_web_lg')

    return nlp

# read the source text into an array consisting of words and punctuation
def read_source_text_into_array(s):
    isword = True
    cur = ""
    full_txt = []

    file = open(s, 'r')
 
    while 1:
     
        # read by character
        char = file.read(1)

        if(isword == True and char != ' ' and char != ',' and char != '.' and char != '?' and char != '!'):
            cur = cur + char
        elif(isword == True and char == ' '):
            isword = False
            full_txt.append(cur)
            cur = ""
        elif(isword == False and (char == ',' or char =='.' or char == '?' or char == '!' or char == ' ')):
            isword = False
        elif(isword == True and (char == '.' or char == ',' or char == '!' or char == '?')):
            isword = False
            full_txt.append(cur)
            full_txt.append(char)
            cur = ""
        elif(isword == False and char != ' ' and char != ',' and char != '.' and char != '?' and char != '!' and char != ''):
            isword = True
            cur = "" + char
          

        if not char: 
            if(isword == True):
                isword = False
                full_txt.append(cur)
                cur = ""
            break
 
    file.close()

    return full_txt

# count the number of words in a source array
def count_num_of_words(s):
    count = 0

    for i in range(len(s)):
        if(s[i] != ',' and s[i] != '.' and s[i] != '?' and s[i] != '!'):
            count = count + 1

    return count

# strip the array of all punctuation leaving just words
def array_just_words(s):
    #count = 0
    new_arr = []

    for i in range(len(s)):
        if(s[i] != ',' and s[i] != '.' and s[i] != '?' and s[i] != '!'):
        #    count = count + 1
            new_arr.append(s[i])

    return new_arr

# truncate the longest source to the size of the smallest source. set the 'template' variable
# to be the smallest source. If both sources are the same size, set 'template' to s1
def truncate():
    num_s1 = count_num_of_words(s1)
    num_s2 = count_num_of_words(s2)
    i = 0

    if(num_s1 == num_s2):
        return s1
    elif(num_s1 > num_s2):
        diff = num_s1 - num_s2

        for j in range(len(s1)):
            if(s1[(len(s1) - 1) - j] != '.' and s1[(len(s1) - 1) - j] != ',' and s1[(len(s1) - 1) - j] != '?' and s1[(len(s1) - 1) - j] != '!'):
                i = i + 1
            del s1[-1]
            if(i == diff):
                break

        return s2
    elif(num_s2 > num_s1):
        diff = num_s2 - num_s1

        for j in range(len(s2)):
            if(s2[(len(s2) - 1) - j] != '.' and s2[(len(s2) - 1) - j] != ',' and s2[(len(s2) - 1) - j] != '?' and s2[(len(s2) - 1) - j] != '!'):
                i = i + 1
            del s2[-1]
            if(i == diff):
                break


        return s1


# print out a source array
def print_arrayed_text(arrayed_text):
    for i in range(len(arrayed_text)):
        if(i < len(arrayed_text) - 1): 
            if(arrayed_text[i + 1] == ',' or arrayed_text[i + 1] == '.' or arrayed_text[i + 1] == '?' or arrayed_text[i + 1] == '!'):
                print(arrayed_text[i], end='')
                print(arrayed_text[i + 1], end='')
            elif(arrayed_text[i] == ',' or arrayed_text[i] == '.' or arrayed_text[i] == '?' or arrayed_text[i] == '!'):
                print(" ", end='')
            elif(arrayed_text[i] != ',' and arrayed_text[i] != '.' and arrayed_text[i] != '?' and arrayed_text[i] != '!'):
                print(arrayed_text[i], end='')
                print(" ", end='')
        else:
            if(arrayed_text[i] == ',' or arrayed_text[i] == '.' or arrayed_text[i] == '?' or arrayed_text[i] == '!'):
                print(" ", end='')
            elif(arrayed_text[i] != ',' and arrayed_text[i] != '.' and arrayed_text[i] != '?' and arrayed_text[i] != '!'):
                print(arrayed_text[i], end='')
                print(" ", end='')

def blend(s1_num, ind_f, ind_t, connection):
    s2_num = 1.0 - s1_num
    blended_array = []
    blended_vec = []

    for i in range(ind_f, ind_t):    
        p = np.array(nlp.vocab[s1[i]].vector)
        o = np.array(nlp.vocab[s2[i]].vector)


        p *= s1_num
        o *= s2_num

        blended_vec = p + o

 
        ms = nlp.vocab.vectors.most_similar(np.asarray([blended_vec]), n=13)
        words = [nlp.vocab.strings[w] for w in ms[0][0]]

        blended_array = blended_array + [words[12].lower()]

        
    connection.send(blended_array)
    

def blend_main(percentage):
    if(percentage == 1.0):
        return s1
    elif(percentage == 0.0):
        return s2
    else:
        conn1, conn2 = multiprocessing.Pipe()
        conn3, conn4 = multiprocessing.Pipe()
        conn5, conn6 = multiprocessing.Pipe()
        conn7, conn8 = multiprocessing.Pipe()
        conn9, conn10 = multiprocessing.Pipe()
    
        num_of_processes = 5
        send_arr = []
        rec_arr =[]
        proc_arr = []
        num_of_chunk = 0
        num_of_last_chunk = 0
    
        num_of_chunk = math.floor(len(template) / num_of_processes)
        if(len(template) % num_of_processes == 0):
            num_of_last_chunk = 0
        else:
            num_of_last_chunk = len(template) % num_of_processes

        process1 = Process(target=blend, args=(percentage, 0, num_of_chunk, conn2))
        process2 = Process(target=blend, args=(percentage, num_of_chunk, num_of_chunk * 2, conn4))
        process3 = Process(target=blend, args=(percentage, num_of_chunk * 2, num_of_chunk * 3, conn6))
        process4 = Process(target=blend, args=(percentage, num_of_chunk * 3, num_of_chunk * 4, conn8))
        process5 = Process(target=blend, args=(percentage, num_of_chunk * 4, num_of_chunk * 5 + num_of_last_chunk, conn10))

        process1.start()
        process2.start()
        process3.start()
        process4.start()
        process5.start()

   
        process1.join()
        process2.join()
        process3.join()
        process4.join()
        process5.join()

        modified_array1 = conn1.recv()
        modified_array2 = conn3.recv()
        modified_array3 = conn5.recv()
        modified_array4 = conn7.recv()
        modified_array5 = conn9.recv()

        final_array = modified_array1 + modified_array2 + modified_array3 + modified_array4 + modified_array5

        return final_array

# output an array containing blur_n elements either side of pos
def get_surrounding_words(pos, blur_n):
    counter = 1
    surrounding_words_array = []

    if(result_array != None):
        while(counter <= blur_n):
            if(pos + counter > len(result_array) - 1):
                surrounding_words_array = surrounding_words_array + [result_array[(pos + counter) - (len(result_array))]]
            else:
                surrounding_words_array = surrounding_words_array + [result_array[pos + counter]]

            if(pos - counter < 0):
                surrounding_words_array = surrounding_words_array + [result_array[(len(result_array) + (pos - counter))]]
            else:
                surrounding_words_array = surrounding_words_array + [result_array[pos - counter]]

            counter = counter + 1

    return surrounding_words_array

#doc = nlp('train knight')
#train, knight = doc[0].vector, doc[1].vector

#new_word = train * 0.5 + knight * 0.5

#ms = nlp.vocab.vectors.most_similar(np.asarray([new_word]), n=20)
#words = [nlp.vocab.strings[w] for w in ms[0][0]]
#print(words)

def convert_word_array_to_vector_array(wa):
    va = []

    for i in range(len(wa)):
        va = va + [nlp.vocab[wa[i]].vector]

    return va

def get_mean_vector_array(va):
    numpy_va = np.array(va)
    return numpy_va.mean(axis = 0)


def blur(x, ind_f, ind_t, connection):
    blurred_array = []

    for i in range(ind_f, ind_t):
        mean = get_mean_vector_array(convert_word_array_to_vector_array(get_surrounding_words(i, x)))
        
        ms = nlp.vocab.vectors.most_similar(np.asarray([mean]), n=13)
        words = [nlp.vocab.strings[w] for w in ms[0][0]]

        blurred_array = blurred_array + [words[12].lower()]

    connection.send(blurred_array)

def blur_main(x):
    if(x == 0):
        return result_array
    else:
        conn1, conn2 = multiprocessing.Pipe()
        conn3, conn4 = multiprocessing.Pipe()
        conn5, conn6 = multiprocessing.Pipe()
        conn7, conn8 = multiprocessing.Pipe()
        conn9, conn10 = multiprocessing.Pipe()
    
        num_of_processes = 5
        send_arr = []
        rec_arr =[]
        proc_arr = []
        num_of_chunk = 0
        num_of_last_chunk = 0
    
        num_of_chunk = math.floor(len(result_array) / num_of_processes)
        if(len(result_array) % num_of_processes == 0):
            num_of_last_chunk = 0
        else:
            num_of_last_chunk = len(result_array) % num_of_processes

        process1 = Process(target=blur, args=(x, 0, num_of_chunk, conn2))
        process2 = Process(target=blur, args=(x, num_of_chunk, num_of_chunk * 2, conn4))
        process3 = Process(target=blur, args=(x, num_of_chunk * 2, num_of_chunk * 3, conn6))
        process4 = Process(target=blur, args=(x, num_of_chunk * 3, num_of_chunk * 4, conn8))
        process5 = Process(target=blur, args=(x, num_of_chunk * 4, num_of_chunk * 5 + num_of_last_chunk, conn10))

        process1.start()
        process2.start()
        process3.start()
        process4.start()
        process5.start()

   
        process1.join()
        process2.join()
        process3.join()
        process4.join()
        process5.join()

        modified_array1 = conn1.recv()
        modified_array2 = conn3.recv()
        modified_array3 = conn5.recv()
        modified_array4 = conn7.recv()
        modified_array5 = conn9.recv()

        final_array = modified_array1 + modified_array2 + modified_array3 + modified_array4 + modified_array5

        return final_array

def create_axis(arr):
    axis = []

    for i in range(len(arr)):
        axis = axis + [i]

    return axis

def chunk_convert_vector_array_to_word_array(va, ind_f, ind_t, connection):
    wa = []

    for i in range(ind_f, ind_t):
        ms = nlp.vocab.vectors.most_similar(np.asarray([va[i]]), n=13)
        words = [nlp.vocab.strings[w] for w in ms[0][0]]

        wa = wa + [words[12].lower()]

    connection.send(wa)

def resize(n):
    if(n == 1.0):
        return result_array
    else:
        x_axis = create_axis(result_array)
        y_axis = convert_word_array_to_vector_array(result_array)

        f = interp1d(x_axis,y_axis, axis= 0, kind='nearest')

        x_new = np.linspace(0, len(result_array) - 1, math.floor(len(result_array) * n), endpoint = True)
        y_new = f(x_new)

        conn1, conn2 = multiprocessing.Pipe()
        conn3, conn4 = multiprocessing.Pipe()
        conn5, conn6 = multiprocessing.Pipe()
        conn7, conn8 = multiprocessing.Pipe()
        conn9, conn10 = multiprocessing.Pipe()
    
        num_of_processes = 5
        send_arr = []
        rec_arr =[]
        proc_arr = []
        num_of_chunk = 0
        num_of_last_chunk = 0
    
        num_of_chunk = math.floor(len(y_new) / num_of_processes)
        if(len(y_new) % num_of_processes == 0):
            num_of_last_chunk = 0
        else:
            num_of_last_chunk = len(y_new) % num_of_processes

        process1 = Process(target=chunk_convert_vector_array_to_word_array, args=(y_new, 0, num_of_chunk, conn2))
        process2 = Process(target=chunk_convert_vector_array_to_word_array, args=(y_new, num_of_chunk, num_of_chunk * 2, conn4))
        process3 = Process(target=chunk_convert_vector_array_to_word_array, args=(y_new, num_of_chunk * 2, num_of_chunk * 3, conn6))
        process4 = Process(target=chunk_convert_vector_array_to_word_array, args=(y_new, num_of_chunk * 3, num_of_chunk * 4, conn8))
        process5 = Process(target=chunk_convert_vector_array_to_word_array, args=(y_new, num_of_chunk * 4, num_of_chunk * 5 + num_of_last_chunk, conn10))

        process1.start()
        process2.start()
        process3.start()
        process4.start()
        process5.start()

        process1.join()
        process2.join()
        process3.join()
        process4.join()
        process5.join()

        modified_array1 = conn1.recv()
        modified_array2 = conn3.recv()
        modified_array3 = conn5.recv()
        modified_array4 = conn7.recv()
        modified_array5 = conn9.recv()

        resized_array = modified_array1 + modified_array2 + modified_array3 + modified_array4 + modified_array5

        return resized_array

def arrayed_text_to_str(result_array):
    str_all = ""

    for i in range(len(result_array)):
        if(i < len(result_array) - 1): 
            if(result_array[i + 1] == ',' or result_array[i + 1] == '.' or result_array[i + 1] == '?' or result_array[i + 1] == '!'):
                str_all = str_all + result_array[i]
                str_all = str_all + result_array[i + 1]
            elif(result_array[i] == ',' or result_array[i] == '.' or result_array[i] == '?' or result_array[i] == '!'):
                str_all = str_all + " "
            elif(result_array[i] != ',' and result_array[i] != '.' and result_array[i] != '?' and result_array[i] != '!'):
                str_all = str_all + result_array[i]
                str_all = str_all + " "
        else:
            if(result_array[i] == ',' or result_array[i] == '.' or result_array[i] == '?' or result_array[i] == '!'):
                str_all = str_all + " "
            elif(result_array[i] != ',' and result_array[i] != '.' and result_array[i] != '?' and result_array[i] != '!'):
                str_all = str_all + result_array[i]
                str_all = str_all + " "

    return str_all


def generate(blend_percentage, x, n):
    global result_array
    global generated_text

    start_time = time.time()
    result_array = blend_main(float(blend_percentage/100))
    generated_text = arrayed_text_to_str(result_array)
    execution_time = time.time() - start_time
    print("Num of words s1:")
    print(count_num_of_words(s1))
    print("Num of words s2:")
    print(count_num_of_words(s2))
    print("BLEND")
    print(f"Execution time in seconds: {execution_time:.6f}")
    print("Num of words generated:")
    print(count_num_of_words(result_array))

    start_time = time.time()
    result_array = blur_main(x)
    generated_text = arrayed_text_to_str(result_array)
    execution_time = time.time() - start_time
    print("Num of words s1:")
    print(count_num_of_words(s1))
    print("Num of words s2:")
    print(count_num_of_words(s2))
    print("BLUR")
    print(f"Execution time in seconds: {execution_time:.6f}")
    print("Num of words generated:")
    print(count_num_of_words(result_array))

    start_time = time.time()
    result_array = resize(n/10)
    generated_text = arrayed_text_to_str(result_array)
    execution_time = time.time() - start_time
    print("Num of words s1:")
    print(count_num_of_words(s1))
    print("Num of words s2:")
    print(count_num_of_words(s2))
    print("RESIZE")
    print(f"Execution time in seconds: {execution_time:.6f}")
    print("Num of words generated:")
    print(count_num_of_words(result_array))

    print("===================================")

def write_results_to_file(str):
    with open("results", "w") as text_file:
        text_file.write(str)  # Replace with your desired string


def change_blend_value(value):
    global blend_value
    blend_value = value

def change_blur_value(value):
    global blur_value
    blur_value = value

def change_resize_value(value):
    global resize_value
    resize_value = value

nlp = initialise()
s1 = read_source_text_into_array('s1')
s2 = read_source_text_into_array('s2')

s1 = array_just_words(s1)
s2 = array_just_words(s2)

template = truncate()
template = array_just_words(template)

app = QApplication(sys.argv)

window = QMainWindow()
central_widget = QWidget()
central_widget.resize(600,600)
layout_all = QVBoxLayout()
layout_sliders_all = QHBoxLayout()
layout_blend_slider_all = QVBoxLayout()
layout_blend_slider = QHBoxLayout()
layout_blur_slider_all = QVBoxLayout()
layout_blur_slider = QHBoxLayout() 
layout_resize_slider_all = QVBoxLayout()
layout_resize_slider = QHBoxLayout() 

# create a textbox
text = QLabel()
text.setFixedWidth(675)
text.setFixedHeight(675)
text.setWordWrap(True)

# Create the blend label
blend_label = QLabel()
blend_label.setText("BLEND")
blend_label.setAlignment(Qt.AlignCenter)

# Create the blend current value label
blend_current_value = QLabel()
blend_current_value.setAlignment(Qt.AlignCenter)
blend_current_value.setText("100")

# Create the blend minimum value label
blend_minimum_value = QLabel()
blend_minimum_value.setText("s2")

# Create the blend maximum value label
blend_maximum_value = QLabel()
blend_maximum_value.setText("s1")

# Create the blend slider
slider_blend = QSlider(Qt.Horizontal)
slider_blend.setRange(0, 100)  # Set min and max values
slider_blend.setValue(100)  # Set initial value
slider_blend.setTickPosition(QSlider.TicksAbove)
slider_blend.valueChanged[int].connect(lambda: blend_current_value.setText(str(slider_blend.value())))
slider_blend.valueChanged[int].connect(change_blend_value)

# loyout the blend slider 
layout_blend_slider_all.addWidget(blend_label)
layout_blend_slider_all.addLayout(layout_blend_slider)
layout_blend_slider_all.addWidget(blend_current_value)
layout_blend_slider.addWidget(blend_minimum_value)
layout_blend_slider.addWidget(slider_blend)
layout_blend_slider.addWidget(blend_maximum_value)

# Create the blur label
blur_label = QLabel()
blur_label.setText("BLUR")
blur_label.setAlignment(Qt.AlignCenter)

# Create the blur current value label
blur_current_value = QLabel()
blur_current_value.setAlignment(Qt.AlignCenter)
blur_current_value.setText("5")

# Create the blur minimum value label
blur_minimum_value = QLabel()
blur_minimum_value.setText("0")

# Create the blur maximum value label
blur_maximum_value = QLabel()
blur_maximum_value.setText("5")

# Create the blur slider
slider_blur = QSlider(Qt.Horizontal)
slider_blur.setRange(0, 5)  # Set min and max values
slider_blur.setValue(5)  # Set initial value
slider_blur.setTickPosition(QSlider.TicksAbove)
slider_blur.valueChanged[int].connect(lambda: blur_current_value.setText(str(slider_blur.value())))
slider_blur.valueChanged[int].connect(change_blur_value)

# nest loyouts the blend slider 
layout_blur_slider_all.addWidget(blur_label)
layout_blur_slider_all.addLayout(layout_blur_slider)
layout_blur_slider_all.addWidget(blur_current_value)
layout_blur_slider.addWidget(blur_minimum_value)
layout_blur_slider.addWidget(slider_blur)
layout_blur_slider.addWidget(blur_maximum_value)

# Create the resize label
resize_label = QLabel()
resize_label.setText("RESIZE")
resize_label.setAlignment(Qt.AlignCenter)

# Create the blend current value label
resize_current_value = QLabel()
resize_current_value.setAlignment(Qt.AlignCenter)
resize_current_value.setText("2.5")

# Create the blend minimum value label
resize_minimum_value = QLabel()
resize_minimum_value.setText("0.5")

# Create the blend maximum value label
resize_maximum_value = QLabel()
resize_maximum_value.setText("2.5")

# Create the resize slider
slider_resize = QSlider(Qt.Horizontal)
slider_resize.setRange(5, 25)  # Set min and max values
slider_resize.setValue(25)  # Set initial value
slider_resize.setTickPosition(QSlider.TicksAbove)
slider_resize.valueChanged[int].connect(lambda: resize_current_value.setText(str(slider_resize.value()/10)))
slider_resize.valueChanged[int].connect(change_resize_value)

# nest loyouts the resize slider 
layout_resize_slider_all.addWidget(resize_label)
layout_resize_slider_all.addLayout(layout_resize_slider)
layout_resize_slider_all.addWidget(resize_current_value)
layout_resize_slider.addWidget(resize_minimum_value)
layout_resize_slider.addWidget(slider_resize)
layout_resize_slider.addWidget(resize_maximum_value)

# Create the execute button
button = QPushButton("Generate!")

layout_all.addWidget(text)

# nest layouts
layout_sliders_all.addLayout(layout_blend_slider_all)
layout_sliders_all.addLayout(layout_blur_slider_all)
layout_sliders_all.addLayout(layout_resize_slider_all)
layout_sliders_all.addWidget(button)

layout_all.addLayout(layout_sliders_all)

# Add slider to layout
#layout_sliders_all.addWidget(slider_blur)
#layout_sliders_all.addWidget(slider_resize)
#layout_sliders_all.addWidget(button)

# Add layout to widget
central_widget.setLayout(layout_all)

    # Set the central widget and show the window
window.setCentralWidget(central_widget)
window.show()

button.clicked.connect(lambda: generate(blend_value, blur_value, resize_value))
button.clicked.connect(lambda: text.setText(generated_text))
button.clicked.connect(lambda: write_results_to_file(generated_text))

sys.exit(app.exec_())
