import torch
from math import sqrt as sqrt
from itertools import product as product

class PriorBoxTme_v1(object):
    """Compute priorbox coordinates in center-offset form for each source
    feature map.
    Note:
    This 'layer' has changed between versions of the original SSD
    paper, so we include both versions, but note v is the most tested and most
    recent version of the paper.

    """

    def __init__(self, cfg):
        super(PriorBoxTme_v1, self).__init__()
        # self.type = cfg.name
        self.image_size_w = cfg['min_dim_w']
        self.image_size_h = cfg['min_dim_h']
        # number of priors for feature map location (either 4 or 6)
        self.num_priors = len(cfg['aspect_ratios'])
        self.variance = cfg['variance'] or [0.1]
        self.feature_maps_w = cfg['feature_maps_w']
        self.feature_maps_h = cfg['feature_maps_h']
        self.min_sizes = cfg['min_sizes']
        self.max_sizes = cfg['max_sizes']
        self.steps_w = cfg['steps_w']
        self.steps_h = cfg['steps_h']
        self.aspect_ratios = cfg['aspect_ratios']
        self.clip = cfg['clip']
        # version is v2_512 or v2_300
        self.version = cfg['name']
        for v in self.variance:
            if v <= 0:
                raise ValueError('Variances must be greater than 0')

    def forward(self):
        mean = []
        # TODO merge these
        for k, (f_w, f_h) in enumerate(zip(self.feature_maps_w, self.feature_maps_h)):
            # for i, j in product(range(f), repeat=2):
            for i in range(f_h):
                for j in range(f_w):
                    f_k_w = self.image_size_w / self.steps_w[k]
                    f_k_h = self.image_size_h / self.steps_h[k]
                    # unit center x,y
                    cx = (j + 0.5) / f_k_w
                    cy = (i + 0.5) / f_k_h

                    # aspect_ratio: 1
                    # rel size: min_size
                    s_k_w = self.min_sizes[k] / (self.image_size_w )
                    s_k_h = self.min_sizes[k] / self.image_size_h
                    mean += [cx, cy, s_k_w, s_k_h]

                    # aspect_ratio: 1
                    # rel size: sqrt(s_k * s_(k+1))
                    s_k_prime_w = sqrt(s_k_w * (self.max_sizes[k] / (self.image_size_w )))
                    s_k_prime_h = sqrt(s_k_h * (self.max_sizes[k] / self.image_size_h))
                    mean += [cx, cy, s_k_prime_w, s_k_prime_h]

                    # rest of aspect ratios
                    for ar in self.aspect_ratios[k]:
                        mean += [cx, cy, s_k_w*sqrt(ar), s_k_h/sqrt(ar)]
                        mean += [cx, cy, s_k_w/sqrt(ar), s_k_h*sqrt(ar)]

        # back to torch land
        output = torch.Tensor(mean).view(-1, 4)
        if self.clip:
            output.clamp_(max=1, min=0)
        return output
