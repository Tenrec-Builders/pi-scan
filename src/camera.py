import os, sys, traceback
import chdkptp
from lupa import LuaError
import errorlog

def search():
  result = []
  try:
    devices = chdkptp.list_devices()
    if devices is not None:
      for info in chdkptp.list_devices():
        result.append(info)
  except LuaError as e:
    errorlog.write('Failed to search: LuaError: ' + str(e.args) + '\nTraceback: ' + traceback.format_exc())
  except Exception as e:
    errorlog.write('Failed to search: ' + str(e.args) + '\n' + traceback.format_exc())
  return result

class Camera:
  def __init__(self, info, config):
    # Tungsten whitebalance for most cameras is 3
    self.whitebalance = 3
    if info.product_id == 12970:
      # Tungsten whitebalance for ELPH 160 cameras is 4
      self.whitebalance = 4
    self.device = chdkptp.ChdkDevice(info)
    self.serial = info.serial_num
    self.zoom_steps = 128
    self.settings = {
      #'zoom': 25,
      #'whitebalance': 'tungsten',
      #'focus': 'auto',
      #'iso': 80
      }
    self.isReady = False
    self.message = ''
    self.position = 'odd'
    
    # TODO Warning about unsupported cameras?

  def log(self, message):
    errorlog.write(self.position + ' camera: ' + message + ' -- self.message: ' + self.message)

  ###########################################################################

  def prepare(self):
    success = False
    if self.isReady:
      success = True
    else:
      try:
        if self.is_connected():
          self.prepare_mode()
          self.prepare_flash()
          self.prepare_zoom()
          self.prepare_nd_filter()
          self.prepare_whitebalance()
          self.prepare_quality()
          self.prepare_resolution()
          success = True
          self.isReady = True
        else:
          self.message = 'Lost connection before prepare capture'
          self.log('Failed while preparing: ' + self.message)
      except Exception as e:
        self.log('Failed while preparing: ' + str(e.args) + '\n' + traceback.format_exc())
    return success

  def prepare_mode(self):
    self.message = 'Error while checking record mode'
    if self.device.mode != 'record':
      self.message = 'Error while switching to record mode'
      self.device.switch_mode('record')
    self.message = 'Error while entering CHDK alt mode'
    self.device.lua_execute('enter_alt(); sleep(50);', do_return=False)
    self.message = 'Error while switching to P mode'
    self.device.lua_execute('set_capture_mode(2);sleep(50);', do_return=False)

  def prepare_zoom(self):
    self.message = 'Failed to set zoom'
    self.device.lua_execute('set_zoom(25);sleep(250);', do_return=False)

  def prepare_nd_filter(self):
    self.message = 'Failed to disable nd filter'
    self.device.lua_execute('set_nd_filter(2);sleep(50);', do_return=False)

  # Set whitebalance to Tungsten
  def prepare_whitebalance(self):
    self.message = 'Failed to set white balance'
    self.device.lua_execute("set_prop(require('propcase').WB_MODE, " + str(self.whitebalance) + ");sleep(50);", do_return=False)
    
  def prepare_flash(self):
    self.message = 'Failed to disable flash'
    #self.device.lua_execute(
    #  "props = require(\"propcase\")\n"
    #  "if(get_flash_mode()~=2) then set_prop(props.FLASH_MODE, 2) end;sleep(50);",
    #  do_return=False)
    self.device.lua_execute(
      "props = require(\"propcase\")\n"
      "set_prop(props.FLASH_MODE, 2);sleep(50);",
      do_return=False)

  def prepare_quality(self):
    self.message = 'Failed to set quality'
    self.device.lua_execute("set_prop(require('propcase').QUALITY, 0);sleep(50);", do_return=False)
    
  def prepare_resolution(self):
    self.message = 'Failed to set resolution'
    self.device.lua_execute("set_prop(require('propcase').RESOLUTION, 0);sleep(50);", do_return=False)
  
  ###########################################################################

  def is_connected(self):
    return self.device.is_connected

  def refocus(self):
    success = False
    try:
      if self.is_connected():
        self.message = 'Error during refocus'
        self.device.lua_execute("set_aflock(1);sleep(50);", do_return=False)
        success = True
      else:
        self.message = 'Lost connection before refocus'
        self.log('Failed to refocus: ' + self.message)
    except Exception as e:
      self.log('Failed to refocus: ' + str(e.args) + '\n' + traceback.format_exc())
    return success
    
  def connect(self):
    success = False
    try:
      self.message = 'Failed during reconnect'
      if not self.device.is_connected:
        self.device.reconnect()
      success = True
    except Exception as e:
      self.log('Failed to connect: ' + str(e.args) + '\n' + traceback.format_exc())
    return success

  ###########################################################################

  def capture(self):
    result = None
    try:
      self.message = 'Failed before shooting'
      if self.isReady and self.is_connected():
        #options = {
        #  'shutter_speed': chdkptp.util.shutter_to_tv96(0.1),
        #  'market_iso': 80,
        #  'stream': True
        #  }
        self.message = 'Failed while shooting'
        data = self.shoot(self.makeOptions())
        if data:
          result = data
          self.device.lua_execute('enter_alt(); sleep(50);', do_return=False)
        else:
          self.message = 'Got empty data back when capturing'
          self.log(self.message)
      elif not self.isReady:
        self.message = 'Tried to capture before preparing camera'
      else:
        self.message = 'Lost connection before capture'
    except Exception as e:
      self.log('Failed to capture: ' + str(e.args) + '\n' + traceback.format_exc())
    return result

  ###########################################################################

  def makeOptions(self):
    options = {}
    options['svm'] = 80
    options['shutter_speed'] = chdkptp.util.shutter_to_tv96(0.1)
    options['nd'] = 2
    options['fformat'] = 1
    luaOptions = self.device._lua.table(**options)
    return self.device._lua.globals.util.serialize(luaOptions)

  def shoot(self, options):
  #def _shoot_streaming(self, options, dng=False):
    self.message = 'Remote shoot intialization failed'
    self.device.lua_execute(
        "return rs_init(%s)" % options, remote_libs=['rs_shoot_init'])
    # TODO: Check for errors
    self.message = 'Remote shoot failed'
    self.device.lua_execute("rs_shoot(%s)" % options,
                     remote_libs=['rs_shoot'], wait=False)
    self.message = 'Populating image data failed'
    rcopts = {}
    img_data = self.device._lua.table()
    rcopts['jpg'] = self.device._lua.globals.chdku.rc_handler_store(img_data)
    self.message = 'Connecting to get capture data failed'
    self.device._con.capture_get_data_pcall(
        self.device._con, self.device._lua.table(**rcopts))
    self.message = 'Waiting for connection to finish failed'
    self.device._con.wait_status_pcall(
        self.device._con, self.device._lua.table(run=False, timeout=30000))
    # TODO: Check for error
    # TODO: Check for timeout
    self.message = 'Initializing USB capture failed'
    self.device.lua_execute('init_usb_capture(0)')
    # NOTE: We can't touch the chunk data from Python or else the
    # Lua runtime segfaults, so we let Lua take care of assembling
    # the output data
    self.message = 'Assembling output data failed'
    result = self.device._lua.eval("""
        function(chunks)
            local size = 0
            for i, c in ipairs(chunks) do
                size = size + c.size
            end
            local buf = lbuf.new(size)
            local offset = 0
            for i, c in ipairs(chunks) do
                if c.offset ~= nil then
                    offset = c.offset
                end
                buf:fill(c.data, offset, 1)
                offset = offset + c.size
            end
            return buf:string()
        end
        """)(img_data)
    return result
  
  ###########################################################################

  def getRomLog(self, position, path):
    self.message = 'Failed to construct pathname of log file'
    filename = path + '/debug/' + position + '-rom.log'

    self.message = 'Failed to delete old rom log from SD Card'
    os.system('rm -f ' + filename)

    self.message = 'Failed to generate new rom log on camera'
    self.device.lua_execute(
      'call_event_proc("SystemEventInit");'
      'call_event_proc("System.Create");'
      'if (os.stat("A/ROMLOG.LOG")) then '
      '  os.remove("A/ROMLOG.LOG");'
      'end '
      'call_event_proc("GetLogToFile","A/ROMLOG.LOG",1);'
      'sleep(2000)', do_return=False)

    self.message = 'Failed to fetch new rom log from camera'
    log = self.device.download_file('ROMLOG.LOG', filename)

    self.message = 'Failed to delete rom log from camera'
    self.device.lua_execute(
      'if (os.stat("A/ROMLOG.LOG")) then '
      '  os.remove("A/ROMLOG.LOG");'
      'end ', do_return=False)

  ###########################################################################

  #def getConfig(self):
  #  configText = '{ "zoom": 20, "whitebalance": "Tungsten" }'
  #  try:
  #    configText = self.device.download_file('pi-scan.conf')
  #  except Exception as e:
  #    self.log('Failed to download configuration file: ' + str(e) + ': ' + str(e.args))
  #  result = {}
  #  try:
  #    result = JSON.parse(configText)
  #  except Exception as e:
  #    self.log('Failed to parse configuration file: ' + str(e) + ': ' +
  #             str(e.args) + '\n' + configText)
  #  return result

  ###########################################################################

  #def setConfig(self, config):
  #  configText = JSON.stringify(config)
    
  
  ###########################################################################

def main():
  cameras = search()
  for camera in cameras:
    camera.setup()
  print cameras

#main()
