import dbus

def search():
  bus = dbus.SystemBus()
  udisks = dbus.Interface(
    bus.get_object('org.freedesktop.UDisks2',
                   '/org/freedesktop/UDisks2'),
    'org.freedesktop.DBus.ObjectManager')
  listDevices = udisks.get_dbus_method('GetManagedObjects')
  result = []
  for key, value in listDevices().items():
    try:
      if ('org.freedesktop.UDisks2.Block' in value and
          'org.freedesktop.UDisks2.Filesystem' in value):
        block = value['org.freedesktop.UDisks2.Block']
        drive = dbus.Interface(
          bus.get_object('org.freedesktop.UDisks2',
                         block['Drive']),
          'org.freedesktop.UDisks2.Drive')
        driveprop = dbus.Interface(
          drive,
          'org.freedesktop.DBus.Properties')
        busType = driveprop.Get('org.freedesktop.UDisks2.Drive',
                                'ConnectionBus')
        if busType == 'usb':
          result.append(Stick(key))
    except Exception as e:
      pass
  return result

def searchAndUnmount(shouldForce):
  result = 0
  sticks = search()
  for stick in sticks:
    if stick.get_mount_point() is not None:
      result += 1
      stick.unmount(shouldForce)
  return result

class Stick:
  def __init__(self, path):
    self.path = path

  def mount(self):
    mount_point = self.get_mount_point()
    try:
      if mount_point is None:
        bus = dbus.SystemBus()
        fs = dbus.Interface(
          bus.get_object('org.freedesktop.UDisks2',
                         self.path),
          'org.freedesktop.UDisks2.Filesystem')
        mount = fs.get_dbus_method(
          "Mount",
          dbus_interface="org.freedesktop.UDisks2.Filesystem")
        mount_point = mount([])
    except Exception, e:
      print 'Failed to mount: ', e
    return mount_point

  def get_mount_point(self):
    mount_point = None
    try:
      bus = dbus.SystemBus()
      fs = dbus.Interface(
        bus.get_object('org.freedesktop.UDisks2',
                       self.path),
        'org.freedesktop.UDisks2.Filesystem')
      fsprop = dbus.Interface(fs, 'org.freedesktop.DBus.Properties')
      old_mounts = fsprop.Get('org.freedesktop.UDisks2.Filesystem',
                              'MountPoints')
      if len(old_mounts) > 0:
        mount_point = bytearray(old_mounts[0]).decode('utf-8')
    except Exception, e:
      print 'Failed to get/parse mount point', e
    return mount_point

  def unmount(self, should_force):
    mount_point = self.get_mount_point()
    try:
      if mount_point is not None:
        bus = dbus.SystemBus()
        fs = dbus.Interface(
          bus.get_object('org.freedesktop.UDisks2',
                         self.path),
          'org.freedesktop.UDisks2.Filesystem')
        unmount = fs.get_dbus_method(
          "Unmount",
          dbus_interface="org.freedesktop.UDisks2.Filesystem")
        unmount({'force': should_force})
    except Exception, e:
      print 'Failed to unmount: ', e

def main():
  mount_point = None
  sticks = search()
  if len(sticks) == 0:
    print 'No Stick Found'
  elif len(sticks) > 1:
    print len(sticks), ' sticks found. Try unplugging one.'
  else:
    mount_point = sticks[0].get_mount_point()
    if mount_point is None:
      mount_point = sticks[0].mount()
      print 'Mounted at: ' + mount_point
    else:
      print 'Unmounting. Was mounted at: ' + mount_point
      sticks[0].unmount(True)

#main()

