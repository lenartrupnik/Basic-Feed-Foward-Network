import pandas as pd
import numpy as np
import pickle
import sys
import matplotlib.pyplot as plt
import math

## scikit 

class Network(object):
    def __init__(self, sizes, optimizer="sgd"):
        # weights connect two layers, each neuron in layer L is connected to every neuron in layer L+1,
        # the weights for that layer of dimensions size(L+1) X size(L)
        # the bias in each layer L is connected to each neuron in L+1, the number of weights necessary for the bias
        # in layer L is therefore size(L+1).
        # The weights are initialized with a He initializer: https://arxiv.org/pdf/1502.01852v1.pdf
        self.weights = [((2/sizes[i-1])**0.5)*np.random.randn(sizes[i], sizes[i-1]) for i in range(1, len(sizes))]
        self.biases = [np.zeros((x, 1)) for x in sizes[1:]]
        self.optimizer = optimizer
        self.layers = len(sizes)
        self.lmbd = 0.05
        
        if self.optimizer == "adam":
            self.momentum_dw, self.v_dw = [0 for i in range(1, len(sizes))], [0 for i in range(1, len(sizes))]
            self.momentum_db, self.v_db = [0 for i in range(1, len(sizes))], [0 for i in range(1, len(sizes))]
            

    def train(self, training_data,training_class, val_data, val_class, epochs, mini_batch_size, eta, regularization=True, decay_rate = True):
        # training data - numpy array of dimensions [n0 x m], where m is the number of examples in the data and
        # n0 is the number of input attributes
        # training_class - numpy array of dimensions [c x m], where c is the number of classes
        # epochs - number of passes over the dataset
        # mini_batch_size - number of examples the network uses to compute the gradient estimation
        
        iteration_index = 1
        eta_current = eta
        self.regularization = regularization
        self.batch_size = training_data.shape[1]
        losses = []
        loss_eval = []
        acc_val = []
        
        for j in range(epochs):
            print("Epoch"+str(j))
            loss_avg = 0.0
            
            mini_batches = [
                (training_data[:,k:k + mini_batch_size], training_class[:,k:k+mini_batch_size])
                for k in range(0, self.batch_size, mini_batch_size)]

            for mini_batch in mini_batches:
                output, Zs, As = self.forward_pass(mini_batch[0])
                gw, gb = None, None
                
                # Implement the learning rate schedule for Task 5
                eta_current = eta * math.exp(-decay_rate * iteration_index)
                
                # Use different backward pass based on the regularization
                if self.regularization:
                    gw, gb = net.backward_pass_regularization(output, mini_batch[1], Zs, As)
                    
                else:
                    gw, gb = net.backward_pass(output, mini_batch[1], Zs, As)

                self.update_network(gw, gb, eta_current, iteration = iteration_index)                

                loss = cross_entropy(mini_batch[1], output)
                loss_avg += loss
            
            iteration_index += 1
            
            # Plot losses
            loss_val, acc = self.eval_network(val_data, val_class)
            loss_eval.append(loss_val)
            losses.append(loss_avg/len(mini_batches))
            acc_val.append(acc)
            
            print("Epoch {} complete".format(j))
            print("Loss:" + str(loss_avg / len(mini_batches)))
        
        # Plot losses, accuracy
        plt.figure(1)
        plt.subplot(211)
        plt.plot(loss_eval, label = "Validation Loss")
        plt.plot(losses, label = "Training loss")
        plt.title("Loss comparison (training - validation)")
        plt.ylabel("Loss")
        plt.xlabel("Epochs")
        plt.legend()
        
        plt.subplot(212)
        plt.plot(acc_val, label = "Accuracy")
        plt.legend()
        plt.title("Validation accuracy")
        plt.xlabel("Epochs")
        plt.ylabel("Accuracy")
        plt.show()



    def eval_network(self, validation_data,validation_class):
        # validation data - numpy array of dimensions [n0 x m], where m is the number of examples in the data and
        # n0 is the number of input attributes
        # validation_class - numpy array of dimensions [c x m], where c is the number of classes
        n = validation_data.shape[1]
        loss_avg = 0.0
        tp = 0.0
        for i in range(validation_data.shape[1]):
            example = np.expand_dims(validation_data[:,i],-1)
            example_class = np.expand_dims(validation_class[:,i],-1)
            example_class_num = np.argmax(validation_class[:,i], axis=0)
            output, Zs, activations = self.forward_pass(example)
            output_num = np.argmax(output, axis=0)[0]
            tp += int(example_class_num == output_num)

            loss = cross_entropy(example_class, output)
            loss_avg += loss
        print("Validation Loss:" + str(loss_avg / n))
        print("Classification accuracy: "+ str(tp/n))
        return loss_avg / n, tp/n

    def update_network(self, gw, gb, eta, beta1 = 0.9, beta2 = 0.999, epsilon = 1e-8, iteration = 0):
        # gw - weight gradients - list with elements of the same shape as elements in self.weights
        # gb - bias gradients - list with elements of the same shape as elements in self.biases
        # eta - learning rate
        # SGD
        if self.optimizer == "sgd" and self.regularization:
            for i in range(len(self.weights)):
                self.weights[i] = (1- self.lmbd * eta/ self.batch_size) * self.weights[i] - eta * gw[i]
                self.biases[i] -= eta * gb[i]
                
        elif self.optimizer == "sgd" and not self.regularization:
            for i in range(len(self.weights)):
                self.weights[i] -= eta * gw[i]
                self.biases[i] -= eta * gb[i]
                
        elif self.optimizer == "adam":
            for i in range(len(self.weights)):
                self.momentum_dw[i] = self.momentum_dw[i] * beta1 + (1-beta1) * gw[i]
                self.momentum_db[i] = self.momentum_db[i] * beta1 + (1-beta1) * gb[i]
                
                self.v_dw[i] = beta2 * self.v_dw[i] + (1 - beta2) * (gw[i]**2)
                self.v_db[i] = beta2 * self.v_db[i] + (1 - beta2) * (gb[i]**2)
                
                momentum_dw_corr = self.momentum_dw[i] / (1 - beta1)
                momentum_db_corr = self.momentum_db[i] / (1 - beta1)
                
                v_dw_corr = self.v_dw[i] / (1 - beta2)
                v_db_corr = self.v_db[i] / (1 - beta2)
            
                self.weights[i] -= eta * (momentum_dw_corr/(np.sqrt(v_dw_corr) + epsilon))
                self.biases[i] -= eta * (momentum_db_corr/(np.sqrt(v_db_corr) + epsilon))
                    
        else:
            raise ValueError('Unknown optimizer:'+ self.optimizer)


    def forward_pass(self, input):
        # input - numpy array of dimensions [n0 x m], where m is the number of examples in the mini batch and
        # n0 is the number of input attributes
        ########## Implement the forward pass
        
        As = [input]
        Zs = []
        activation = input
        for w, b in zip(self.weights[:-1], self.biases[:-1]):
            z = np.dot(w, activation) + b
            a = sigmoid(z)

            Zs.append(z)
            As.append(a)
            activation = a
        
        z = np.dot(self.weights[-1], activation) + self.biases[-1]
        Zs.append(z)
        As.append(softmax(z))
        output = As[-1]

        return output, Zs, As
        

    def backward_pass_regularization(self, output, target, Zs, activations):
        dBs = [np.zeros(b.shape) for b in self.biases]
        dWs = [np.zeros(w.shape) for w in self.weights]
        
        
        dZ = softmax_dLdZ(output, target)
        dW = np.dot(dZ, activations[-2].transpose()) + (self.lmbd / self.batch_size) * self.weights[-1]
        dB = np.sum(dZ, axis=1, keepdims=True)
        dAPrev = np.dot(self.weights[-1].transpose(), dZ)
        
        dWs[-1] = dW
        dBs[-1] = dB
        
        for l in range(self.layers -2, 0, -1):
            dZ = dAPrev * sigmoid_prime(Zs[l-1])
            dW = np.dot(dZ, activations[l-1].transpose()) + (self.lmbd / self.batch_size) * self.weights[l-1]
            dB =  np.sum(dZ, axis=1, keepdims=True)
            
            if l > 1:
                dAPrev = np.dot(self.weights[l-1].transpose(), dZ)
                
            dWs[l-1] = dW
            dBs[l-1] = dB
        return dWs, dBs       
    
    def backward_pass(self, output, target, Zs, activations):
        dBs = [np.zeros(b.shape) for b in self.biases]
        dWs = [np.zeros(w.shape) for w in self.weights]
        
        dZ = softmax_dLdZ(output, target)
        dW = np.dot(dZ, activations[-2].transpose()) 
        dB = np.sum(dZ, axis=1, keepdims=True)
        dAPrev = np.dot(self.weights[-1].transpose(), dZ)
        
        dWs[-1] = dW
        dBs[-1] = dB
        
        for l in range(self.layers -2, 0, -1):
            dZ = dAPrev * sigmoid_prime(Zs[l-1])
            dW = np.dot(dZ, activations[l-1].transpose())
            dB =  np.sum(dZ, axis=1, keepdims=True)
            
            if l > 1:
                dAPrev = np.dot(self.weights[l-1].transpose(), dZ)
                
            dWs[l-1] = dW
            dBs[l-1] = dB
        return dWs, dBs 
    
    
def softmax(Z):
    expZ = np.exp(Z - np.max(Z))
    return expZ / expZ.sum(axis=0, keepdims=True)

def softmax_dLdZ(output, target):
    # partial derivative of the cross entropy loss w.r.t Z at the last layer
    return output - target

def cross_entropy(y_true, y_pred, epsilon=1e-12):
    targets = y_true.transpose()
    predictions = y_pred.transpose()
    predictions = np.clip(predictions, epsilon, 1. - epsilon)
    N = predictions.shape[0]
    ce = -np.sum(targets * np.log(predictions + 1e-9)) / N 
    return ce

def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-z))

def sigmoid_prime(z):
    return sigmoid(z) * (1 - sigmoid(z))

def unpickle(file):
    with open(file, 'rb') as fo:
        return pickle.load(fo, encoding='bytes')

def load_data_cifar(train_file, test_file):
    train_dict = unpickle(train_file)
    test_dict = unpickle(test_file)
    train_data = np.array(train_dict['data']) / 255.0
    train_class = np.array(train_dict['labels'])
    train_class_one_hot = np.zeros((train_data.shape[0], 10))
    train_class_one_hot[np.arange(train_class.shape[0]), train_class] = 1.0
    test_data = np.array(test_dict['data']) / 255.0
    test_class = np.array(test_dict['labels'])
    test_class_one_hot = np.zeros((test_class.shape[0], 10))
    test_class_one_hot[np.arange(test_class.shape[0]), test_class] = 1.0
    return train_data.transpose(), train_class_one_hot.transpose(), test_data.transpose(), test_class_one_hot.transpose()

if __name__ == "__main__":
    train_file = "./data/train_data.pckl"
    test_file = "./data/test_data.pckl"
    train_data, train_class, test_data, test_class = load_data_cifar(train_file, test_file)
    val_pct = 0.1
    val_size = int(len(train_data) * val_pct)
    val_data = train_data[..., :val_size]
    val_class = train_class[..., :val_size]
    train_data = train_data[..., val_size:]
    train_class = train_class[..., val_size:]
    # The Network takes as input a list of the numbers of neurons at each layer. The first layer has to match the
    # number of input attributes from the data, and the last layer has to match the number of output classes
    # The initial settings are not even close to the optimal network architecture, try increasing the number of layers
    # and neurons and see what happens.
    net = Network([train_data.shape[0],512, 256, 128, 10], optimizer="adam")
    net.train(train_data,train_class, val_data, val_class, 30, 64, 0.0005, regularization=True, decay_rate=0.005)
    net.eval_network(test_data, test_class)
