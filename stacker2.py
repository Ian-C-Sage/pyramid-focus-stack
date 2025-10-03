import os
import errno
import itertools
import cv2
import numpy as np
import copy
import pickle
from PySide6.QtCore import QObject, QThread, Signal

# Given a 3-channel colour image, construct both colour and grayscale
# Laplacian pyramid representations. For every layer in the pyramid,
# a weight is provided which is set to 1.0, but may be altered from
# a routine outside the class. The set of weights is then used to
# bias the contribution of each layer when the image is reconstructed
# by the restore routine.
class dual_laplacian():
    colour_stack=[]
    mono_stack=[]
    weights=[]

    def __init__(self, input_image=None, min_size=1):
        self.colour_stack=[]
        self.mono_stack=[]
        if type(input_image)==type(self):
            for entry in input_image.colour_stack:
                self.colour_stack.append(np.zeros_like(entry))
            for entry in input_image.mono_stack:
                self.mono_stack.append(np.zeros_like(entry))
            
        elif type(input_image)==type(None):
            return None
        elif len(input_image.shape)<3:
            return None
        else:
            mono_image=cv2.cvtColor(input_image, cv2.COLOR_BGR2GRAY)
            cur_colour=input_image.astype(np.float64)
            cur_mono=mono_image.astype(np.float64)
            #cur_colour=input_image.copy()
            #cur_mono=mono_image.copy()
            shape=cur_mono.shape
            while min(shape)>min_size:
                next_colour=cv2.pyrDown(cur_colour)
                blur_colour=cv2.pyrUp(next_colour, dstsize=(shape[1], shape[0]))
                self.colour_stack.append(cv2.subtract(cur_colour, blur_colour))

                next_mono=cv2.pyrDown(cur_mono)
                blur_mono=cv2.pyrUp(next_mono, dstsize=(shape[1], shape[0]))
                self.mono_stack.append(cv2.subtract(cur_mono, blur_mono))

                cur_colour=next_colour.copy()
                cur_mono=next_mono.copy()
                shape=cur_mono.shape
                #print(shape)
            self.colour_stack.append(cur_colour)
            self.mono_stack.append(cur_mono)
            #for entry in self.colour_stack:
            #    print(entry.shape)
        self.weights=[]
        for layer in self.colour_stack:
            self.weights.append(1.0)

             
    def restore(self):
        terms=len(self.colour_stack)
        image=self.colour_stack[-1].copy()
        image=image*self.weights[-1]
        for index in range(terms-1, 0, -1):
            #print(index)
            image=cv2.pyrUp(image, dstsize=(self.colour_stack[index-1].shape[1], self.colour_stack[index-1].shape[0]))
            image=cv2.add(image, self.weights[index-1]*self.colour_stack[index-1])
        print(np.max(image))
        return image

    def save(self, filename):
        opf=open(filename, 'wb')
        pickle.dump(self, opf, pickle.HIGHEST_PROTOCOL)
        opf.close()


# Given a 3-channel colour image, construct only a colour Laplacian
# pyramid representation. For every layer in the pyramid, a weight
# is provided which is set to 1.0, but may be altered from a routine
# outside the class. The set of weights may be used to bias the
# contribution of each layer when the image is reconstructed by the
# restore routine.
class laplacian():
    colour_stack=[]
    weights=[]

    def __init__(self, input_image=None, min_size=1):
        self.colour_stack=[]
        if type(input_image)==type(self):
            for entry in input_image.colour_stack:
                self.colour_stack.append(np.zeros_like(entry))
        elif type(input_image)==type(None):
            return None
        elif len(input_image.shape)<3:
            return None
        else:
            cur_colour=input_image.astype(np.float64)
            shape=cur_colour.shape[:2]
            while min(shape)>min_size:
                next_colour=cv2.pyrDown(cur_colour)
                blur_colour=cv2.pyrUp(next_colour, dstsize=(shape[1], shape[0]))
                self.colour_stack.append(cv2.subtract(cur_colour, blur_colour))

                cur_colour=next_colour.copy()
                shape=cur_colour.shape[:2]
                #print(shape)
            self.colour_stack.append(cur_colour)
            #for entry in self.colour_stack:
            #    print(entry.shape)
        self.weights=[]
        for layer in self.colour_stack:
            self.weights.append(1.0)

             
    def restore(self):
        terms=len(self.colour_stack)
        image=self.colour_stack[-1].copy()
        image=image*self.weights[-1]
        for index in range(terms-1, 0, -1):
            image=cv2.pyrUp(image, dstsize=(self.colour_stack[index-1].shape[1], self.colour_stack[index-1].shape[0]))
            image=cv2.add(image, self.weights[index-1]*self.colour_stack[index-1])
        print(np.max(image))
        return image

    def save(self, filename):
        opf=open(filename, 'wb')
        pickle.dump(self, opf, pickle.HIGHEST_PROTOCOL)
        opf.close()



class stacker(QObject):
    finished=Signal()
    abandoned=Signal()
    progress=Signal(int)
    message=Signal(str)

    def __init__(self, params):
        super().__init__(None)
        self.input_path=params[0]
        self.output_file=params[1]
        self.filter_size=params[2]
        self.save_pyramid=params[3]
        self.by_channel=params[4]
        self.scale_output=params[5]
    
    def get_image_list(self, input_path):
        try:
            inputs=os.walk(input_path)
            path, _, fn_list=next(inputs)
        except:
            return []
        image_files = sorted(fn_list)
        return image_files
        
    def pascal(self, level):
        if level==1:
            return [1]
        elif level==2:
            return[1, 1]
        else:
            gen=self.pascal(level-1)
            res=[1]
            for index in range(len(gen)-1):
                res.append(gen[index]+gen[index+1])
            res.append(1)
        return res

    def window(self, size):
        a=self.pascal(size)
        b=np.outer(a, a)
        c=sum(sum(b))
        return b/c

    def gray_energy(self, image, kernel):
        res=np.square(image)
        return cv2.filter2D(res, ddepth=-1, kernel=kernel, borderType=cv2.BORDER_REFLECT_101)

    def channel_energy(self, image, channel, kernel):
        res=np.square(image[:, :, channel])
        return cv2.filter2D(res, ddepth=-1, kernel=kernel, borderType=cv2.BORDER_REFLECT_101)


    # Fuse images according to gray pyramid dominance
    def fuse_stack_by_gray(self, source_dir, image_names, kernel_size):
        self.message.emit("Stacking by gray")
        my_kernel=self.window(kernel_size)
        for index, name in enumerate(image_names):
            #print("Processing ", name)
            prog=int(100*index/len(image_names))
            self.progress.emit(prog)
            image = cv2.imread(source_dir+'/'+name, cv2.IMREAD_UNCHANGED) 
            lap=dual_laplacian(image)
            if index==0:
                result=dual_laplacian(lap)
            for level, matrix in enumerate(result.mono_stack):
                res_energy=self.gray_energy(matrix, my_kernel)
                ip_energy=self.gray_energy(lap.mono_stack[level], my_kernel)
                threshold=np.greater(ip_energy, res_energy)
                result.colour_stack[level]=result.colour_stack[level]+(lap.colour_stack[level]-result.colour_stack[level])*threshold[:, :, np.newaxis]
                result.mono_stack[level]=result.mono_stack[level]+(lap.mono_stack[level]-result.mono_stack[level])*threshold
        self.precision=image.dtype
        return result

    # Fuse each colour channel separately
    def fuse_stack_by_channel(self, source_dir, image_names, kernel_size):
        self.message.emit("Stacking by colour channel")
        my_kernel=self.window(kernel_size)
        for index, name in enumerate(image_names):
            prog=int(100*index/len(image_names))
            self.progress.emit(prog)
            image = cv2.imread(source_dir+'/'+name, cv2.IMREAD_UNCHANGED)
            lap=laplacian(image)
            if index==0:
                result=laplacian(lap)
            for level, matrix in enumerate(result.colour_stack):
                for channel in range(3):
                    res_energy=self.channel_energy(matrix, channel, my_kernel)
                    ip_energy=self.channel_energy(lap.colour_stack[level], channel, my_kernel)
                    threshold=np.greater(ip_energy, res_energy)
                    result.colour_stack[level][:, :, channel]=result.colour_stack[level][:, :, channel]+(lap.colour_stack[level][:, :, channel]-result.colour_stack[level][:, :, channel])*threshold
        self.precision=image.dtype      
        return result
    


    def run(self):
        image_list=self.get_image_list(self.input_path)
        #print(image_list)
        exclude=[]
        for name in image_list:
            if name.lower()[:6]=='output':
                exclude.append(name)
        #print(exclude)
        for name in exclude:
            image_list.remove(name)
        #print(image_list)
        if len(image_list)<2:
            self.message.emit("Not enough images in source directory!")
            self.abandoned.emit()
            return
        #print("Reached fuse stack")
        if self.by_channel==True:
            res=self.fuse_stack_by_channel(self.input_path, image_list, self.filter_size)
        else:
            res=self.fuse_stack_by_gray(self.input_path, image_list, self.filter_size)
        if self.save_pyramid:
            res.save(self.input_path+'/output.pyr')
        #print("Reached restore")
        image=res.restore()
        #print("Restore complete")
        if self.scale_output==False:
            if self.precision==np.uint8:
                cv2.imwrite(self.output_file, image.clip(0, 255).astype(np.uint8))
            elif self.precision==np.uint16:
                cv2.imwrite(self.output_file, image.clip(0, 65535).astype(np.uint16))
        else:
            if self.precision==np.uint8:
                image=np.uint8((image-np.min(image))*255.0/(np.max(image)-np.min(image)))
                #print(np.max(image), np.min(image))
                cv2.imwrite(self.output_file, image)
            elif self.precision==np.uint16:
                image=np.uint16((image-np.min(image))*65535.0/(np.max(image)-np.min(image)))
                #print(np.max(image), np.min(image))
                cv2.imwrite(self.output_file, image)


        self.message.emit("Wrote output as "+str(self.precision))
        self.finished.emit()

if __name__=="__main__":
    param_list=["/home/ian/snowdrops/2025_02_20/png/set4a/aligned", "/home/ian/snowdrops/2025_02_20/png/set4a/aligned/output3.png", 5, False, False]
    #param_list=["/home/ian/test_images", "/home/ian/test_images/output.png", 5, False, False]
    a=stacker(param_list)
    a.run()
