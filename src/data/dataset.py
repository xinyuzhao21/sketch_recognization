# https://discuss.pytorch.org/t/how-to-split-dataset-into-test-and-validation-sets/33987
# https://github.com/adambielski/siamese-triplet/blob/master/datasets.py
import torch
import torchvision
import numpy as np
from PIL import Image
from torchvision import transforms

class ImageDataset(torchvision.datasets.ImageFolder):
    def __init__(self, image_root, transform=None, labels=None,train=True,eval=False):
        self.image_root = image_root
        self.train_paths = []
        self.test_paths = []
        self.train = train
        train_links = self.image_root+'/train.txt'
        test_links = self.image_root + '/test.txt'
        if eval:
            test_links = self.image_root+'/valid.txt'
        with open(train_links) as f:
            for line in f:
                self.train_paths.append(line.split()[1])
        self.transform = transform
        with open(test_links) as f:
            for line in f:
                self.test_paths.append(line.split()[1])
        super(ImageDataset, self).__init__(image_root,is_valid_file=self.is_valid,transform=self.transform)

    def is_valid(self,path):
        return (not (path in self.test_paths) ) == self.train

class PairedDataset(torch.utils.data.Dataset):
    'Characterizes a dataset for PyTorch'
    def __init__(self,sketch_root,photo_root,transform=None,train=True,eval=False, fine_grain=False):
        'Initialization'

        self.sketch_root = sketch_root
        self.photo_root = photo_root
        self.train_sketch,self.train_photo = [],[]
        self.test_sketch,self.test_photo = [],[]
        self.label_to_indx_sketch = {}
        self.label_to_indx_photo = {}
        self.train = train
        self.fine_grain = fine_grain
        self._make_dataset()
        self.transform = transform

    def pil_loader(self,path: str) -> Image.Image:
        # open path as file to avoid ResourceWarning (https://github.com/python-pillow/Pillow/issues/835)
        with open(path, 'rb') as f:
            img = Image.open(f)
            return img.convert('RGB')

    def _make_dataset(self):

        self.classes = []
        self.class_to_index = {}
        self.length = 0
        if self.train:
            train_links= self.sketch_root+'/train.txt'

            class_i =0
            with open(train_links) as f:
                for i,line in enumerate(f):
                    label,path = line.split()

                    if label not in self.class_to_index:
                        self.class_to_index[label] = class_i
                        self.classes.append(label)
                        class_i+=1
                    label = self.class_to_index[label]
                    self.train_sketch.append((label, path))

                    if label not in self.label_to_indx_sketch:
                        self.label_to_indx_sketch[label]=[]

                    self.label_to_indx_sketch[label].append(i)

            self.length = len(self.train_sketch)
            train_links= self.photo_root+'/train.txt'
            with open(train_links) as f:
                for i,line in enumerate(f):
                    label, path = line.split()
                    label = self.class_to_index[label]
                    if label not in self.label_to_indx_photo:
                        self.label_to_indx_photo[label] = []
                    self.label_to_indx_photo[label].append(i)
                    self.train_photo.append((label, path))
        else:
            # generate fixed pairs for testing
            test_links = self.sketch_root + '/test.txt'

            class_i = 0
            with open(test_links) as f:
                for i, line in enumerate(f):
                    label, path = line.split()

                    if label not in self.class_to_index:
                        self.class_to_index[label] = class_i
                        self.classes.append(label)
                        class_i += 1
                    label = self.class_to_index[label]
                    self.test_sketch.append((label, path))

                    if label not in self.label_to_indx_sketch:
                        self.label_to_indx_sketch[label] = []

                    self.label_to_indx_sketch[label].append(i)
            self.length = len(self.test_sketch)
            test_links = self.photo_root + '/test.txt'
            with open(test_links) as f:
                for i, line in enumerate(f):
                    label, path = line.split()
                    label = self.class_to_index[label]
                    if label not in self.label_to_indx_photo:
                        self.label_to_indx_photo[label] = []
                    self.label_to_indx_photo[label].append(i)
                    self.test_photo.append((label, path))




        self.classes_set = set(self.classes)
        self.classes.append('unmatched')
        self.class_to_index['unmatched'] = len(self.classes)-1


    def __len__(self):
        'Denotes the total number of samples'
        return self.length

    def __getitem__(self, index):
        'Generates one sample of data'
        # Select sample
        random_state = np.random.RandomState(123)
        target = np.random.randint(0, 2)
        label_s,sketch = self.train_sketch[index]
        label = label_s
        if self.train:
            if target ==1:
                photo_index = random_state.choice(self.label_to_indx_photo[label_s])
                label_p,photo = self.train_photo[photo_index]
            else:
                neg_class = random_state.choice(list(self.classes_set-set([self.classes[label_s]])))
                neg_class = self.class_to_index[neg_class]
                photo_index = random_state.choice(self.label_to_indx_photo[neg_class])
                label_p,photo = self.train_photo[photo_index]
                label = self.class_to_index['unmatched']
        else:
            random_state = np.random.RandomState(29)
            if target ==1:
                photo_index = random_state.choice(self.label_to_indx_photo[label_s])
                label_p,photo = self.train_photo[photo_index]
            else:
                neg_class = random_state.choice(list(self.classes_set-set([self.classes[label_s]])))
                neg_class = self.class_to_index[neg_class]
                photo_index = random_state.choice(self.label_to_indx_photo[neg_class])
                label_p,photo = self.train_photo[photo_index]
                label = self.class_to_index['unmatched']
        sketch =self.pil_loader(sketch)
        photo = self.pil_loader(photo)
        if self.transform is not None:
            sketch=self.transform(sketch)
            photo = self.transform(photo)
        # return (sketch,photo,label_s,label_p), (label, target)

        return (sketch, photo), label