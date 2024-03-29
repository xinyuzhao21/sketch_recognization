import torch, os
from loss.contrastive import ContrastiveLoss
from torchvision.transforms import ToTensor, Compose, Resize, Grayscale
# from torch.utils import tensorboard as tb
from model.sketchanet import SketchANet, Net
from model.siamesenet import SiameseNet,SiaClassNet
from model.resnet import getResnet
import data.dataset as DataSet
from torch.utils.data import DataLoader
from torchvision.datasets import ImageFolder
from torchvision import transforms
import data.datautil as util
import torchvision
from model.linear import ClassificationNet

def set_checkpoint(epoch, model, optimizer, loss, path):
    torch.save({
        'epoch': epoch,
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'loss': loss,
    }, path)


def load_checkpoint(path, model, optimizer):
    checkpoint = torch.load(path)
    model.load_state_dict(checkpoint['model_state_dict'])
    optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
    epoch = checkpoint['epoch']
    loss = checkpoint['loss']
    print("Checkpoint loaded", 'epoch', epoch, 'loss', loss)



def main():
    # batch_size = 100
    batch_size = 1
    balanced = False
    print("here")
    # sk_root ='../test'
    in_size = 225
    in_size = 224
    tmp_root = '../256x256/photo/tx_000000000000'
    sketch_root = '../256x256/sketch/tx_000000000000'
    # tmp_root = '../rendered_256x256/256x256/photo/tx_000000000000'
    # sketch_root = '../rendered_256x256/256x256/sketch/tx_000000000000'
    tmp_root = '../test_pair/photo'
    sketch_root = '../test_pair/sketch'
    train_dataset = DataSet.PairedDataset(photo_root=tmp_root,sketch_root=sketch_root,transform=Compose([Resize(in_size), ToTensor()]),balanced=balanced)
    train_dataloader = DataLoader(train_dataset, batch_size=batch_size, pin_memory=True, num_workers=os.cpu_count(),
                                  shuffle=True, drop_last=True)

    test_dataset = DataSet.ImageDataset(sketch_root, transform=Compose([Resize(in_size), ToTensor()]),train=True)
    # print(test_dataset.classes)
    # print(train_dataset.classes)
    # print(test_dataset.class_to_idx)
    # print(train_dataset.class_to_index)
    test_dataloader = DataLoader(test_dataset, batch_size=batch_size, pin_memory=True, num_workers=os.cpu_count(),
                         shuffle=True, drop_last=True)

    num_class = len(train_dataset.classes)
    embedding_size = 200
    net1 = getResnet(num_class=embedding_size, pretrain=True)
    model = SiaClassNet(net1,embedding_size,num_class)

    method = "classify"
    crit = torch.nn.CrossEntropyLoss()
    model.train()

    if torch.cuda.is_available():
        model = model.cuda()

    optim = torch.optim.Adam(model.parameters())
    # optimizer = optim.SGD(model.parameters(), lr=0.001, momentum=0.9)
    # Tensorboard stuff
    # writer = tb.SummaryWriter('./logs')

    count = 0
    epochs = 200
    prints_interval = 1
    max_chpt = 3
    max_loss = -1
    for e in range(epochs):
        print('epoch', e, 'started')
        avg_loss = 0
        for i, (X, Y) in enumerate(train_dataloader):

            if torch.cuda.is_available():
                X, Y =(X[0].cuda(),X[1].cuda()), (Y[0].cuda(),Y[1].cuda(),Y[2].cuda)
            sketch,photo =X
            optim.zero_grad()
            to_image = transforms.ToPILImage()
            #output = model(*X)
            output = model(sketch,sketch)
            (Y,label_s,label_p) = Y
            # loss = crit(output, Y)
            loss = crit(output, label_s)
            avg_loss+=loss.item()
            if i % prints_interval == 0:
                print(output,label_s)
                print(f'[Training] {i}/{e}/{epochs} -> Loss: {avg_loss/(i+1)}')
                # writer.add_scalar('train-loss', loss.item(), count)
            loss.backward()

            optim.step()

            count += 1
        print('epoch', e, 'Avg loss', avg_loss/len(train_dataloader))

        eval_accu(test_dataloader,model,e,epochs)

        # model.eval()

        # model.train()
def eval_loss(test_dataloader,model,e,epochs,crit,train_dataset):
    avg_loss = 0
    for i, (X, Y) in enumerate(test_dataloader):

        if torch.cuda.is_available():
            X, Y = X.cuda(), Y.cuda()
        Y = (Y != train_dataset.class_to_index['unmatched'])
        to_image = transforms.ToPILImage()
        output = model(*X)

        # print(output,Y)
        loss = crit(*output, Y)
        avg_loss += loss.item()
    print(f'[Testing] -/{e}/{epochs} -> Avg Loss: {avg_loss / len(test_dataloader)} %')
    return  avg_loss


def eval_accu(test_dataloader,model,e,epochs):
    correct, total, accuracy = 0, 0, 0
    for i, (X, Y) in enumerate(test_dataloader):

        if torch.cuda.is_available():
            X, Y = X.cuda(), Y.cuda()
        output = model(X,X)
        _, predicted = torch.max(output, 1)
        total += Y.size(0)
        correct += (predicted == Y).sum().item()

    accuracy = (correct / total) * 100

    print(f'[Testing] -/{e}/{epochs} -> Accuracy: {accuracy} %', total, correct)

if __name__ == '__main__':
    #     import argparse
    #
    #     parser = argparse.ArgumentParser()
    #     parser.add_argument('--traindata', type=str, required=True, help='root of the train datasets')
    #     parser.add_argument('--testdata', type=str, required=True, help='root of the test datasets')
    #     parser.add_argument('-b', '--batch_size', type=int, required=False, default=8, help='Batch size')
    #     parser.add_argument('-c', '--num_classes', type=int, required=False, default=10, help='Number of classes for the classification task')
    #     parser.add_argument('-e', '--epochs', type=int, required=False, default=100, help='No. of epochs')
    #     parser.add_argument('-i', '--print_interval', type=int, required=False, default=10, help='Print loss after this many iterations')
    #     args = parser.parse_args()
    #
    main()
