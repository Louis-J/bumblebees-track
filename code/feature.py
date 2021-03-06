import numpy as np
from skimage.filters import prewitt_h, prewitt_v, laplace


class Feature:

    
    # create new Feature object storing 4 images
    def __init__(self, no_flash1, no_flash2, flash, lst_flash, n=5, boxsize=3, r=3):
        self.n = n
        self.boxsize = boxsize
        self.r = r
        self.locs = self.getmaxlocs(flash-no_flash2, n=self.n)
        self.comb_img = [no_flash1, no_flash2, flash, flash-no_flash1, flash-no_flash2, flash-lst_flash]


    # get the top n brightest spots
    def getmaxlocs(self, img, n):
        deleteradius = 20
        locs = []
        cut_img = img[deleteradius:(img.shape[0]-deleteradius), deleteradius:(img.shape[1]-deleteradius)].copy()
        for i in range(n):
            loc = np.unravel_index(cut_img.argmax(), cut_img.shape)
            v = cut_img[loc[0],loc[1]]
            locs.append([loc[0]+deleteradius, loc[1]+deleteradius, v])
            cut_img[(loc[0]-deleteradius):(loc[0]+deleteradius),(loc[1]-deleteradius):(loc[1]+deleteradius)]=-10000
        return np.array(locs)


    # get the boxsize by boxsize cut image of top n brightest dots 
    def get_square_cut(self, img, boxsize):
        cut = []
        for brightest in self.locs:
            x1 = int(brightest[0]-boxsize)
            x2 = int(brightest[0]+boxsize)+1
            y1 = int(brightest[1]-boxsize)
            y2 = int(brightest[1]+boxsize)+1
            cut.append(img[x1:x2, y1:y2].copy())
        return np.array(cut)


    # Get the mean of an image
    def get_mean(self, cut):
        mean = []
        for img in cut:
            mean.append(np.mean(img))
        return np.array(mean)


    # get the standard deviation of an image
    def get_std(self, cut):
        std = []
        for img in cut:
            std.append(np.std(img))
        return np.array(std)


    # get the mean and std of concentric ring of top n brightest dots
    def get_concentric_ring(self, img, r):
        boxsize = int(r)
        cut = []
        for brightest in self.locs:
            x1 = int(brightest[0]-boxsize)
            x2 = int(brightest[0]+boxsize)+1
            y1 = int(brightest[1]-boxsize)
            y2 = int(brightest[1]+boxsize)+1
            circle = img[x1:x2, y1:y2].copy()
            store_lst = []
            for i in range(1, circle.shape[0]+1):
                for j in range(1, circle.shape[1]+1):
                    if (i-r)**2 + (j-r)**2 <= r**2:
                        store_lst.append(circle[i,j])
            store_lst = np.array(store_lst)
        return np.mean(store_lst), np.std(store_lst)


    # edge detection by convolution, and get its mean and std
    def detect_edge(self, cut):
        laplacians = []
        mean = []
        std = []
        for img in cut:
            # convolute with proper kernels
            laplacian = laplace(img)
            laplacians.append(laplacian)
            mean.append(np.mean(laplacian))
            std.append(np.std(laplacian))
        return np.array(laplacians), np.array(mean), np.array(std)


    # get the feature
    def get_feature(self):
        m = len(self.comb_img)
        img_size = (self.boxsize*2+1)**2
        feature_cut = np.zeros((self.n, (img_size+2)*m))
        feature_edge = np.zeros((self.n, (img_size+2)*m))
        feature_ring = np.zeros((self.n, 2*m))
        for i in range(m):
            img = self.comb_img[i]
            cut = self.get_square_cut(img, boxsize=self.boxsize)
            feature_cut[:, i*img_size:(i+1)*img_size] = cut.reshape((self.n, img_size))
            feature_cut[:, img_size*m+i] = self.get_mean(cut)
            feature_cut[:, img_size*m+m+i] = self.get_std(cut)

            edge, edge_mean, edge_std = self.detect_edge(cut)
            feature_edge[:, i*img_size:(i+1)*img_size] = edge.reshape((self.n, img_size))
            feature_edge[:, img_size*m+i] = edge_mean
            feature_edge[:, img_size*m+m+i] = edge_std

            feature_ring[:, i], feature_ring[:, m+i] = self.get_concentric_ring(img, r=self.r)

        feature = np.concatenate((feature_cut, feature_edge, feature_ring), axis=1)
        return feature


    # get the index window of each feature
    def get_index(self):
        index = []
        m = len(self.comb_img)
        img_size = (self.boxsize*2+1)**2
        temp_index = 0
        for j in range(2):
            for i in range(m):
                index.append(temp_index+img_size*(i+1))
            temp_index = index[-1]
            for i in range(2*m):
                index.append(temp_index+i+1)
            temp_index = index[-1]
        for i in range(2*m):
            index.append(temp_index+1+i)
        
        index = [0] + index

        return index

    # get the number of all features
    def get_num_feature(self):
        m = len(self.comb_img)
        img_size = (self.boxsize*2+1)**2
        number = m*img_size*2 +  m*2*3
        return number


    def get_belong_feature(self, index):
        index_window = self.get_index()
        feature_type = ['cut', 'cut_mean', 'cut_std','edge', 'edge_mean', 'edge_std', 'ring_mean', 'ring_std']
        image_type = ['no_flash1', 'no_flash2', 'flash', 'flash-no_flash1', 'flash-no_flash2', 'flash-lst_flash']
        len_type = len(feature_type)
        len_image = len(image_type)
        for i in index:
            for window in index_window[1:]:
                if i < window:
                    order = index_window.index(window)-1
                    image_order = order % len_image
                    feature_order = order // len_image % len_type
                    print('the image is %s and the type of feature is %s' % (image_type[image_order], feature_type[feature_order]))
                    break

        return 0
        