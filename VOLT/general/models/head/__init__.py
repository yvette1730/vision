import torch

from .box.head import BoxHead
# from .keypoint_head.keypoint_head import build_roi_keypoint_head
# from .mask_head.mask_head import build_roi_mask_head


class ROIHeads(torch.nn.ModuleDict):
    """
    Combines individual heads  into a single head.
    """

    def __init__(self, cfg, heads):
        super(CombinedROIHeads, self).__init__(heads)

        self.cfg = cfg.clone()

        if cfg.MODEL.MASK_ON and cfg.MODEL.ROI_MASK_HEAD.SHARE_BOX_FEATURE_EXTRACTOR:
            self.mask.feature_extractor = self.box.feature_extractor
        if cfg.MODEL.KEYPOINT_ON and cfg.MODEL.ROI_KEYPOINT_HEAD.SHARE_BOX_FEATURE_EXTRACTOR:
            self.keypoint.feature_extractor = self.box.feature_extractor

    def forward(
        self,
        features,
        proposals,
        targets=None,
        language_dict_features=None,
        positive_map_label_to_token=None,
    ):

        losses = {}
        detections = proposals

        if self.cfg.MODEL.BOX_ON:
            "TODO rename x to roi_box_features, if it doesn't increase memory consumption"
            x, detections, loss_box = self.box(features, proposals, targets)
            losses.update(loss_box)

        if self.cfg.MODEL.MASK_ON:
            mask_features = features
            # optimization: during training, if we share the feature extractor between
            # the box and the mask heads, then we can reuse the features already computed
            if self.training and self.cfg.MODEL.ROI_MASK_HEAD.SHARE_BOX_FEATURE_EXTRACTOR:
                mask_features = x
            # During training, self.box() will return the unaltered proposals as "detections"
            # this makes the API consistent during training and testing
            x, detections, loss_mask = self.mask(
                mask_features,
                detections,
                targets,
                language_dict_features=language_dict_features,
                positive_map_label_to_token=positive_map_label_to_token,
            )
            losses.update(loss_mask)

        if self.cfg.MODEL.KEYPOINT_ON:
            keypoint_features = features
            # optimization: during training, if we share the feature extractor between
            # the box and the mask heads, then we can reuse the features already computed
            if self.training and self.cfg.MODEL.ROI_KEYPOINT_HEAD.SHARE_BOX_FEATURE_EXTRACTOR:
                keypoint_features = x
            # During training, self.box() will return the unaltered proposals as "detections"
            # this makes the API consistent during training and testing
            x, detections, loss_keypoint = self.keypoint(keypoint_features, detections, targets)
            losses.update(loss_keypoint)
        return x, detections, losses


def build_head(cfg):
    """
    individually create the heads, that will be combined together
    """

    if cfg.MODEL.RPN_ONLY:
        return None

    heads = []
    if cfg.MODEL.BOX_ON:
        heads.append(("box", BoxHead(cfg)))
    # if cfg.MODEL.MASK_ON:
        # heads.append(("mask", build_roi_mask_head(cfg)))
    # if cfg.MODEL.KEYPOINT_ON:
        # heads.append(("keypoint", build_roi_keypoint_head(cfg)))

    return CombinedROIHeads(cfg, heads)
