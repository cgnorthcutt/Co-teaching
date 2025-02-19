import os
import os.path
import copy
import hashlib
import errno
import numpy as np
from numpy.testing import assert_array_almost_equal

def check_integrity(fpath, md5):
    if not os.path.isfile(fpath):
        return False
    md5o = hashlib.md5()
    with open(fpath, 'rb') as f:
        # read in 1MB chunks
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            md5o.update(chunk)
    md5c = md5o.hexdigest()
    if md5c != md5:
        return False
    return True


def download_url(url, root, filename, md5):
    from six.moves import urllib

    root = os.path.expanduser(root)
    fpath = os.path.join(root, filename)

    try:
        os.makedirs(root)
    except OSError as e:
        if e.errno == errno.EEXIST:
            pass
        else:
            raise

    # downloads file
    if os.path.isfile(fpath) and check_integrity(fpath, md5):
        print('Using downloaded and verified file: ' + fpath)
    else:
        try:
            print('Downloading ' + url + ' to ' + fpath)
            urllib.request.urlretrieve(url, fpath)
        except:
            if url[:5] == 'https':
                url = url.replace('https:', 'http:')
                print('Failed download. Trying https -> http instead.'
                      ' Downloading ' + url + ' to ' + fpath)
                urllib.request.urlretrieve(url, fpath)


def list_dir(root, prefix=False):
    """List all directories at a given root

    Args:
        root (str): Path to directory whose folders need to be listed
        prefix (bool, optional): If true, prepends the path to each result, otherwise
            only returns the name of the directories found
    """
    root = os.path.expanduser(root)
    directories = list(
        filter(
            lambda p: os.path.isdir(os.path.join(root, p)),
            os.listdir(root)
        )
    )

    if prefix is True:
        directories = [os.path.join(root, d) for d in directories]

    return directories


def list_files(root, suffix, prefix=False):
    """List all files ending with a suffix at a given root

    Args:
        root (str): Path to directory whose folders need to be listed
        suffix (str or tuple): Suffix of the files to match, e.g. '.png' or ('.jpg', '.png').
            It uses the Python "str.endswith" method and is passed directly
        prefix (bool, optional): If true, prepends the path to each result, otherwise
            only returns the name of the files found
    """
    root = os.path.expanduser(root)
    files = list(
        filter(
            lambda p: os.path.isfile(os.path.join(root, p)) and p.endswith(suffix),
            os.listdir(root)
        )
    )

    if prefix is True:
        files = [os.path.join(root, d) for d in files]

    return files


# basic function
def multiclass_noisify(y, P, random_state=0):
    """ Flip classes according to transition probability matrix T.
    It expects a number between 0 and the number of classes - 1.
    """
    print np.max(y), P.shape[0]
    assert P.shape[0] == P.shape[1]
    assert np.max(y) < P.shape[0]

    # row stochastic matrix
    assert_array_almost_equal(P.sum(axis=1), np.ones(P.shape[1]))
    assert (P >= 0.0).all()

    m = y.shape[0]
    print m
    new_y = y.copy()
    flipper = np.random.RandomState(random_state)

    for idx in np.arange(m):
        i = y[idx]
        # draw a vector with only an 1
        flipped = flipper.multinomial(1, P[i, :][0], 1)[0]
        new_y[idx] = np.where(flipped == 1)[0]

    return new_y


# noisify_pairflip call the function "multiclass_noisify"
def noisify_pairflip(y_train, noise, random_state=None, nb_classes=10):
    """mistakes:
        flip in the pair
    """
    P = np.eye(nb_classes)
    n = noise

    if n > 0.0:
        # 0 -> 1
        P[0, 0], P[0, 1] = 1. - n, n
        for i in range(1, nb_classes-1):
            P[i, i], P[i, i + 1] = 1. - n, n
        P[nb_classes-1, nb_classes-1], P[nb_classes-1, 0] = 1. - n, n

        y_train_noisy = multiclass_noisify(y_train, P=P,
                                           random_state=random_state)
        actual_noise = (y_train_noisy != y_train).mean()
        assert actual_noise > 0.0
        print('Actual noise %.2f' % actual_noise)
        y_train = y_train_noisy
    print P

    return y_train, actual_noise


def noisify_multiclass_symmetric(y_train, noise, random_state=None, nb_classes=10):
    """mistakes:
        flip in the symmetric way
    """
    P = np.ones((nb_classes, nb_classes))
    n = noise
    P = (n / (nb_classes - 1)) * P

    if n > 0.0:
        # 0 -> 1
        P[0, 0] = 1. - n
        for i in range(1, nb_classes-1):
            P[i, i] = 1. - n
        P[nb_classes-1, nb_classes-1] = 1. - n

        y_train_noisy = multiclass_noisify(y_train, P=P,
                                           random_state=random_state)
        actual_noise = (y_train_noisy != y_train).mean()
        assert actual_noise > 0.0
        print('Actual noise %.2f' % actual_noise)
        y_train = y_train_noisy
    print P

    return y_train, actual_noise


def noisify_multiclass_symmetric(y_train, noise, random_state=None, nb_classes=10):
    """mistakes:
        flip in the symmetric way
    """
    P = np.ones((nb_classes, nb_classes))
    n = noise
    P = (n / (nb_classes - 1)) * P

    if n > 0.0:
        # 0 -> 1
        P[0, 0] = 1. - n
        for i in range(1, nb_classes-1):
            P[i, i] = 1. - n
        P[nb_classes-1, nb_classes-1] = 1. - n

        y_train_noisy = multiclass_noisify(y_train, P=P,
                                           random_state=random_state)
        actual_noise = (y_train_noisy != y_train).mean()
        assert actual_noise > 0.0
        print('Actual noise %.2f' % actual_noise)
        y_train = y_train_noisy
    print P

    return y_train, actual_noise


def noisify_from_file(y_train, filename, filenames):
    '''Reads a json file mapping cifar image id to label and returns
    the noisy labels from that file.'''

    import torchvision.transforms as transforms
    import torchvision.datasets as datasets
    import torchvision.models as models
    import json
    import torch

    train_dataset = datasets.ImageFolder(
        "/datasets/datasets/cifar10/cifar10/train/",
        transforms.Compose([
#             transforms.RandomCrop(32, padding=4),
#             transforms.RandomHorizontalFlip(),
            transforms.ToTensor(),
#             transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2023, 0.1994, 0.2010)),
        ]),
    )
    
    true_labels = np.asarray([label for _, label in train_dataset.imgs])
    
    # use noisy training labels instead of dataset labels
    with open(filename, 'r') as rf:
        train_labels_dict = json.load(rf)
    train_dataset.imgs = [(fn, train_labels_dict[fn]) for fn, _ in train_dataset.imgs]
    train_dataset.samples = train_dataset.imgs
    
    train_loader = torch.utils.data.DataLoader(
        train_dataset, batch_size=50000, shuffle=False,
        num_workers=10, pin_memory=True, sampler=None,
    )
    
    for train_data, train_noisy_labels in train_loader:
        pass
    train_data = (train_data.numpy() * 255).astype(np.uint8)
    train_data = train_data.transpose((0, 2, 3, 1))  # convert to HWC
    train_noisy_labels = train_noisy_labels.numpy()
    
#     print(type(train_data), type(train_noisy_labels), train_data.shape, train_noisy_labels.shape)
    
    actual_noise = sum(true_labels != train_noisy_labels) / float(len(true_labels))
    assert actual_noise > 0.0
    print('Actual noise %.2f' % actual_noise)
    
    
#     return 
    
#     print(dir(train_dataset))
    
#     print('Opening', filename)
#     with open(filename, 'rb') as rf:
#         import json
#         d = json.load(rf)
#     d = {k.split("/")[-1]:v for k,v in d.items()}
#     print(filenames)
#     train_noisy_labels = np.asarray([[d[f]] for f in filenames])
# #     print(type(y_train), type(y_train[0]))
# #     y_train = np.asarray([i[0] for i in y_train])
#     print(train_noisy_labels, y_train, len(y_train), len(train_noisy_labels))
#     print((train_noisy_labels != y_train).mean())
#     print(np.bincount(np.asarray([i[0] for i in y_train])))
#     print(np.bincount(np.asarray([i[0] for i in train_noisy_labels])))
#     same_count = 0
#     for i, val in enumerate(y_train):
#         if i % 5000 == 0:
#             print(val, train_noisy_labels[i])
#         same_count += train_noisy_labels[i][0] == val[0]
#     print(same_count)
#     actual_noise = (train_noisy_labels != y_train).mean()
#     assert actual_noise > 0.0
#     print('Actual noise %.2f' % actual_noise)
    
    return np.asarray([[i] for i in train_noisy_labels]), train_data, actual_noise
    

def noisify(dataset='mnist', nb_classes=10, train_labels=None, noise_type=None, noise_rate=0, random_state=0, noise_filename=None, filenames=None):
    if noise_type == 'pairflip':
        train_noisy_labels, actual_noise_rate = noisify_pairflip(train_labels, noise_rate, random_state=0, nb_classes=nb_classes)
    if noise_type == 'symmetric':
        train_noisy_labels, actual_noise_rate = noisify_multiclass_symmetric(train_labels, noise_rate, random_state=0, nb_classes=nb_classes)
    if noise_type == 'from_file':
        return noisify_from_file(train_labels, noise_filename, filenames)
        
    return train_noisy_labels, actual_noise_rate
