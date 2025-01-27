import torch
import getopt
import math
import numpy as np
import os
import PIL
import PIL.Image
import sys
import tempfile
import flowiz
from correlation import correlation # the custom cost volume layer
import runway
from runway.data_types import *
from run import *
from run import estimate
from pathlib import Path

torch.set_grad_enabled(False)
torch.backends.cudnn.enabled = True

@runway.setup(options={"model_file": file(extension=".pytorch")})
def setup(opts):
    checkpoint = opts["model_file"]
    network = Network(checkpoint).cuda().eval()
    
    return network


command_inputs = {"input_image": image}
command_outputs = {"output_image": image}

f = []
initialize = True
@runway.command("compute_flow", inputs=command_inputs, outputs=command_outputs, description="Computes Optical Flow")
def compute_flow(network, inputs):
    global f
    global initialize
    current_frame = np.array(inputs["input_image"])

    if initialize:
        frame = current_frame
        f.append(current_frame)
        initialize = False

    else:
        f.append(current_frame)
        prev_frame = f.pop(0)
        next_frame = f[0]

        tensorFirst = torch.FloatTensor(np.array(prev_frame)[:, :, ::-1].transpose(2, 0, 1).astype(np.float32) * (1.0 / 255.0))
        tensorSecond = torch.FloatTensor(np.array(next_frame)[:, :, ::-1].transpose(2, 0, 1).astype(np.float32) * (1.0 / 255.0))

        tensorOutput = estimate(network, tensorFirst, tensorSecond)
        
        objectOutput = tempfile.NamedTemporaryFile(suffix=".flo")
        out = str(Path(objectOutput.name))
        np.array([80, 73, 69, 72], np.uint8).tofile(objectOutput)
        np.array([tensorOutput.size(2), tensorOutput.size(1)], np.int32).tofile(objectOutput)
        np.array(tensorOutput.numpy().transpose(1, 2, 0), np.float32).tofile(objectOutput)
        
        frame = flowiz.convert_from_file(out)
        

    return {"output_image": frame}


if __name__ == "__main__":
    runway.run()

