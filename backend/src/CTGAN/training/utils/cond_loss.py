import torch
import torch.nn.functional as F

def cond_loss(data, c, m, transformer):
    loss = []
    st = 0
    st_c = 0

    for column_info in transformer.output_info_list:
        for span_info in column_info:
            if len(column_info) != 1 or span_info.activation_fn != 'softmax':
                st += span_info.dim
            else:
                ed = st + span_info.dim
                ed_c = st_c + span_info.dim

                probs = torch.clamp(data[:, st:ed], min=1e-8, max=1)
                labels = torch.argmax(c[:, st_c:ed_c], dim=1)
                ce_loss = F.cross_entropy(probs, labels, reduction='none')
                loss.append(ce_loss)
                st = ed
                st_c = ed_c

    loss = torch.stack(loss, dim=1)

    return (loss * m).sum() / data.size(0)