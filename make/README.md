# Make and Install Scripts

These are a work in progress and are not fully baked yet. There is no error handling and no real documentation yet. There is no provision to exit when something goes wrong and some things are still hard-coded. You might be best off using them as a set of notes and pasting commands into your terminal one by one in order to get things built.

The basic workflow is to start with the latest Raspbian Lite image and then use qemu-arm, chroot, and the loop filesystem to install extra packages and configuration packages onto it.
