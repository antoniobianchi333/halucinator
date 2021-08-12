
# Reproducing the AMP DEMO.

The following instructions explain how to reconstruct the AMP 
demonstration.

HALucinator comprises three components: avatar-qemu, avatar2 and halucinator 
proper.

As we have modified all three components to bring AVR support to HALucinator 
for earlier demonstrations, you will need all three components. 

## Acquiring the source

 - Clone the avatar-qemu tree and switch to the devel branch.

   git clone https://github.com/HexHive/avatar-qemu
   cd avatar-qemu
   git checkout devel
   cd ..

 - Clone the avatar tree

   git clone https://github.com/HexHive/avatar2
   cd avatar2
   git checkout devel
   cd ..

 - Finally, clone the HALucinator tree.
   
   git clone https://github.com/HexHive/halucinator/
   cd halucinator
   git checkout av/amp_demo
   cd ..

## Build Avatar-Qemu

Avatar2 requires Avatar-qemu, a modified version of upstream qemu with 
patches to support Avatar functionality. Avatar2 will not work correctly 
with distribution-provided qemu-system-arm and similar. avatar-qemu can 
however be installed to a non-system location.

To build and install, we generally recommend out of tree builds. To 
perform one, first choose a desired install location. I have chosen `/opt/qemu`; 
yours may be difficult. Note that I have granted my user permissions to this 
directory and none of these operations are run as root:

```
mkdir avatar-qemu-build`.
../avatar-qemu/configure --disable-sdl --target-list=arm-softmmu,avr-softmmu --enable-debug --prefix=/opt/qemu
make -j $(nproc)
make install
cd ..
``` 

## Prepare HALucinator

You will now need to enter the halucinator directly. I typically work inside 
the project folder, but this is not required. So I would then

```
cd halucinator
```

Now create a virtual environment for python, using

```
virtualenv halenv
```

the exact name of the environment is up to you, but it should not clash with 
a directory name inside the directory you are in. Now

```
source halenv/bin/activate
```

this will allow python installations to proceed inside this isolated environment 
rather than your system `site-packages`. No commands require root, and if you 
see permission errors, you are likely trying to install to system locations.

For the next step, install most of the dependencies.

```
pip install -r requirements.txt
```

Once done, it remains to install the avatar2 package. Eventually this will be 
taken care of as part of the requirements.txt / setup.py, but while we have 
changes that are not yet upstreamed, we install our local modifications as 
follows:

```
cd ../avatar2 
```

or otherwise move to the directory where avatar2 (not qemu) is installed. 

**Important** please ignore the install functionality avatar2 provides. While 
useful for upstream, we use Avatar2 in a different way. Instead, simply:

```
pip install -e .
```

To install the local code into your virtualenv. Now return to the halucinator 
directory:

```
cd ../halucinator
```

### Configure general HALucinator settings

Next, you need to tell HALucinator where to find `avatar-qemu`. Inside the 
HALucinator directory, type 

```
less configs/halucinator-config.yaml
```

You should see:

```
---
arm_qemu_location: /opt/qemu/bin/qemu-system-arm
avr_qemu_location: /opt/qemu/bin/qemu-system-avr
qemu_debug: false
gdb_location: /usr/bin/gdb
ipc:
    tx_port: 5556
    rx_port: 5555
```

Edit this file with your favourite editor to modify the qemu locations to 
be accurate. You should have both, although for the purposes of this 
specific demo you will not need the AVR variant.

The IPC functionality should be left as is.

Finally, gdb on RedHat systems supports multiple architectures by default. 
Ubuntu does not. You can see supported architectures by doing this:

```
$ gdb
(gdb) set architecture
Requires an argument. Valid arguments are i386, i386:x86-64, i386:x64-32, 
i8086, i386:intel, i386:x86-64:intel, i386:x64-32:intel, s390:64-bit, 
s390:31-bit, rs6000:6000, rs6000:rs1, rs6000:rsc, rs6000:rs2, 
powerpc:common64, powerpc:common, powerpc:603, powerpc:EC603e, powerpc:604, 
powerpc:403, powerpc:601, powerpc:620, powerpc:630, powerpc:a35, 
powerpc:rs64ii, powerpc:rs64iii, powerpc:7400, powerpc:e500, powerpc:e500mc, 
powerpc:e500mc64, powerpc:MPC8XX, powerpc:750, powerpc:titan, powerpc:vle, 
powerpc:e5500, powerpc:e6500, arm, armv2, armv2a, armv3, armv3m, armv4, 
armv4t, armv5, armv5t, armv5te, xscale, ep9312, iwmmxt, iwmmxt2, armv5tej, 
armv6, armv6kz, armv6t2, armv6k, armv7, armv6-m, armv6s-m, armv7e-m, armv8-a, 
armv8-r, armv8-m.base, armv8-m.main, armv8.1-m.main, arm_any, aarch64, 
aarch64:ilp32, aarch64:armv8-r, auto
```

If you have arm variants in this list, you can use your system's gdb. On Debian 
systems, the following should work:

```
sudo apt install gdb-multiarch
```

then launch `gdb-multiarch` and try the above command. If this contains the arm 
architectures, should point HALucinator at this GDB:

```
gdb_location: /usr/bin/gdb-multiarch
```

Save the file.

### Prepare the demos

Now you actually have everything you need to run the demonstration code. 
Demos are committed under `test/AMP/ch2-stm32-vuln` for example. There 
are two requirements to fulfil here:

 1. The binaries are not committed to git. You will need to supply them from 
    the AMP challenge repository.

    You will need to convert the ELF file to a binary using the following 
    command:

    objcopy -O binary nucleo32-vuln.elf nucleo32-vuln.elf.bin

    Repeat this exercise for any other binaries being tested, in their 
    respective folders.
 2. The `_memories` file describes where to find these binaries. Ensure that 
    the names you have used for the ELF files match in this file, e.g.:

    ```
    memories:
      alias: {base_addr: 0x0, file: nucleo32-vuln.elf.bin,
    permissions: r-x, size: 0x800000}
      flash: {base_addr: 0x8000000, file: nucleo32-vuln.elf.bin,

Caveats:

 1. If the ELF file is not exactly those provided through AMP, it is possible 
    the symbols are different. In which case you will need to recreate the 
    `_addrs.yaml` file. `halucinator-symtool`, a command installed inside the 
    virtualenv, is used to produce these files.
 2. If the ELF file uses firmware with a different or modified HAL, you may 
    need to go through a lengthy process of getting the firmware to work.

### Run

You now need to create a second terminal using whatever emulator you are using. 
In this emulator you should navigate to the `halucinator` directory and 
activate the virtualenv:

```
source halenv/bin/activate
```

In this new terminal, now `cd halucinator/external_devices` and run:

```
python amp_gui.py & 
```

This will launch the external device pretending to be the dashboard. If you 
prefer the command line variant given in previous demos, you can remain in the 
parent halucinator directory and type

```
halucinator-periph -m halucinator.external_devices.cabus
```

Now return to your original terminal. Here you can launch and stop HALucinator. 
From the halucinator repository directory, run for example:


```
./test/AMP/ch2-stm32-vuln/run.sh
```

You can alternatively inspect the script and run its statements directly.

This will rehost the firmware and you can now replicate the AMP demo using the 
GUI.

