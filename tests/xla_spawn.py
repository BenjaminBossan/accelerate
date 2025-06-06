# Copyright 2021 The HuggingFace Team. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
A simple launcher script for TPU training

Inspired by https://github.com/pytorch/pytorch/blob/master/torch/distributed/launch.py

::
    >>> python xla_spawn.py --num_cores=NUM_CORES_YOU_HAVE
               YOUR_TRAINING_SCRIPT.py (--arg1 --arg2 --arg3 and all other
               arguments of your training script)

"""

import importlib
import sys
from argparse import REMAINDER, ArgumentParser
from pathlib import Path

import torch_xla.distributed.xla_multiprocessing as xmp
from torch_xla import device_count


def parse_args():
    """
    Helper function parsing the command line options
    @retval ArgumentParser
    """
    parser = ArgumentParser(
        description=(
            "PyTorch TPU distributed training launch helper utility that will spawn up multiple distributed processes"
        )
    )

    # Optional arguments for the launch helper
    num_devices = device_count()
    parser.add_argument(
        "--num_cores",
        type=int,
        default=num_devices,
        help="Number of TPU cores to use (1 or number of available devices).",
    )

    # positional
    parser.add_argument(
        "training_script",
        type=str,
        help=(
            "The full path to the single TPU training "
            "program/script to be launched in parallel, "
            "followed by all the arguments for the "
            "training script"
        ),
    )

    # rest from the training program
    parser.add_argument("training_script_args", nargs=REMAINDER)

    return parser.parse_args()


def main():
    args = parse_args()

    # Import training_script as a module.
    script_fpath = Path(args.training_script)
    sys.path.append(str(script_fpath.parent.resolve()))
    mod_name = script_fpath.stem
    mod = importlib.import_module(mod_name)

    # Patch sys.argv
    sys.argv = [args.training_script] + args.training_script_args
    num_cores = args.num_cores
    if num_cores == device_count() and num_cores != 1:
        # There is an error in xmp.spawn that causes it to fail when num_cores is specified and not 1, so we set it to
        # None when it matches the number of devices.
        num_cores = None
    xmp.spawn(mod._mp_fn, args=(), nprocs=args.num_cores)


if __name__ == "__main__":
    main()
