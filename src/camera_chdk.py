import os, sys, traceback
import chdkptp
from lupa import LuaError
import errorlog

zoomToFactor = {
  'Min Zoom': 0.0,
  '0.5':      0.05,
  '1':        0.1,
  '1.5':      0.15,
  '2':        0.2,
  '2.5':      0.25,
  '3':        0.3,
  '3.5':      0.35,
  '4':        0.4,
  '4.5':      0.45,
  '5':        0.5,
  '5.5':      0.55,
  '6':        0.6,
  '6.5':      0.65,
  '7':        0.7,
  '7.5':      0.75,
  '8':        0.8,
  '8.5':      0.85,
  '9':        0.9,
  '9.5':      0.95,
  'Max Zoom': 1.0
  }

shutterToFactor = {
  '1/250': 1/250.0,
  '1/125': 1/125.0,
  '1/60':  1/60.0,
  '1/30':  1/30.0,
  '1/25':  1/25.0,
  '1/20':  1/20.0,
  '1/18':  1/18.0,
  '1/16':  1/16.0,
  '1/15':  1/15.0,
  '1/14':  1/14.0,
  '1/12':  1/12.0,
  '1/10':  1/10.0,
  '1/8':   1/8.0,
  '1/6':   1/6.0,
  '1/4':   1/4.0,
  '1/3':   1/3.0,
  '1/2':   1/2.0,
  '1/1':   1/1.0
  }

def search():
  result = []
  try:
    devices = chdkptp.list_devices()
    if devices is not None:
      for info in chdkptp.list_devices():
        if info.chdk_api[0] != -1 or info.chdk_api[1] != -1:
          result.append(info)
  except LuaError as e:
    errorlog.write('Failed to search: LuaError: ' + str(e.args) + '\nTraceback: ' + traceback.format_exc())
  except chdkptp.PTPError as e:
    errorlog.write('Failed to search: PTPError: ' + str(e.args) + '\n' + traceback.format_exc() + '\nPTP Traceback:\n' + e.traceback)
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
    self.zoom_steps = None
    self.config = config
    self.isReady = False
    self.message = ''
    self.position = 'odd'
    self.debugCount = 3
    self.debugFail = ''
    
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
      except chdkptp.PTPError as e:
        self.log('Failed while preparing: PTPError: ' + str(e.args) + '\n' + traceback.format_exc() + '\nPTP Traceback:\n' + e.traceback)
      except Exception as e:
        self.log('Failed while preparing: ' + str(e.args) + '\n' + traceback.format_exc())
    return success

  def prepare_mode(self):
    self.message = 'Error while checking record mode'
    #if self.device.mode != 'record':
    self.message = 'Error while switching to record mode'
    self.device.switch_mode('record')
    self.message = 'Error while entering CHDK alt mode'
    self.device.lua_execute('sleep(50); enter_alt(); sleep(50);', do_return=False)
    self.message = 'Error while switching to P mode'
    self.device.lua_execute('set_capture_mode(2);sleep(50);', do_return=False)

  def prepare_zoom(self):
    self.message = 'Failed to set zoom'
    self.device.lua_execute('set_zoom(%d);sleep(250);' % self.calculate_zoom(),
                            do_return=False)

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
        self.device.lua_execute("sleep(50);press('shoot_half');sleep(500);release('shoot_half');sleep(50);set_aflock(1);sleep(50);", do_return=False)
        success = True
      else:
        self.message = 'Lost connection before refocus'
        self.log('Failed to refocus: ' + self.message)
    except chdkptp.PTPError as e:
      self.log('Failed to refocus: PTPError: ' + str(e.args) + '\n' + traceback.format_exc() + '\nPTP Traceback:\n' + e.traceback)
    except Exception as e:
      self.log('Failed to refocus: ' + str(e.args) + '\n' + traceback.format_exc())
    return success

  def unlockFocus(self):
    success = False
    try:
      if self.is_connected():
        self.message = 'Error during unlock focus'
        self.device.lua_execute("sleep(50);set_aflock(0);sleep(50);", do_return=False)
        success = True
      else:
        self.message = 'Lost connection before unlock focus'
        self.log('Failed to unlock focus: ' + self.message)
    except chdkptp.PTPError as e:
      self.log('Failed to unlock focus: PTPError: ' + str(e.args) + '\n' + traceback.format_exc() + '\nPTP Traceback:\n' + e.traceback)
    except Exception as e:
      self.log('Failed to unlock focus: ' + str(e.args) + '\n' + traceback.format_exc())
    return success
    
  def connect(self):
    success = False
    try:
      self.message = 'Failed during reconnect'
      if not self.device.is_connected:
        self.device.reconnect()
      success = True
    except chdkptp.PTPError as e:
      self.log('Failed to connect: PTPError: ' + str(e.args) + '\n' + traceback.format_exc() + '\nPTP Traceback:\n' + e.traceback)
    except Exception as e:
      self.log('Failed to connect: ' + str(e.args) + '\n' + traceback.format_exc())
    return success


  ###########################################################################

  def calculate_zoom(self):
    if self.zoom_steps is None:
      self.zoom_steps = self.device.lua_execute('sleep(50); return get_zoom_steps()')
    choice = '5'
    if 'zoom' in self.config:
      choice = self.config['zoom']
    factor = 0.5
    if choice in zoomToFactor:
      factor = zoomToFactor[choice]
    return max(round(self.zoom_steps * factor) - 1, 0)

  ###########################################################################

  def calculate_shutter(self):
    choice = '1/15'
    if 'shutter' in self.config:
      choice = self.config['shutter']
    factor = 1/15.0
    if choice in shutterToFactor:
      factor = shutterToFactor[choice]
    return factor
  
  ###########################################################################

  def capture(self, filename):
    result = None
    if self.debugFail == self.position:
      self.debugCount -= 1
      if self.debugCount <= 0:
        self.debugCount = 4
        self.message = 'Testing failure'
        return None
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
          self.message = 'Failed while saving'
          fp = open(filename + '.jpg', 'w')
          fp.write(data)
          fp.close()
          result = filename
          self.message = 'Failed while re-entering alt mode'
          self.device.lua_execute('sleep(50); enter_alt(); sleep(50);', do_return=False)
        else:
          self.message = 'Got empty data back when capturing'
          self.log(self.message)
      elif not self.isReady:
        self.message = 'Tried to capture before preparing camera'
      else:
        self.message = 'Lost connection before capture'
    except chdkptp.PTPError as e:
      self.log('Failed to capture: PTPError: ' + str(e.args) + '\n' + traceback.format_exc() + '\nPTP Traceback:\n' + e.traceback)
    except Exception as e:
      self.log('Failed to capture: ' + str(e.args) + '\n' + traceback.format_exc())
    return result

  ###########################################################################

  def makeOptions(self):
    options = {}
    options['svm'] = chdkptp.util.iso_to_sv96(100)
    options['tv'] = chdkptp.util.shutter_to_tv96(self.calculate_shutter())
    options['nd'] = 2
    options['fformat'] = 1
    luaOptions = self.device._lua.table(**options)
    return self.device._lua.globals.util.serialize(luaOptions)

  def shoot(self, options):
  #def _shoot_streaming(self, options, dng=False):
    self.message = 'Remote shoot intialization failed'
    self.device.lua_execute(
        "sleep(50); return rs_init(%s)" % options, remote_libs=['rs_shoot_init'], do_return=False)
    # TODO: Check for errors
    self.message = 'Remote shoot failed'
    self.device.lua_execute("sleep(50); rs_shoot(%s)" % options,
                     remote_libs=['rs_shoot'], wait=False, do_return=False)
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
    self.device.lua_execute('sleep(50); init_usb_capture(0)', do_return=False)
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
    try:
      os.remove(filename)
    except:
      # Could not remove file. Oh well.
      pass

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

  def beepFail(self):
    try:
      if self.is_connected():
        self.device.lua_execute('sleep(50); play_sound(6)', do_return=False)
    except chdkptp.PTPError as e:
      self.log('Failed to beep: PTPError: ' + str(e.args) + '\n' + traceback.format_exc() + '\nPTP Traceback:\n' + e.traceback)
    except Exception as e:
      self.log('Failed to beep: ' + str(e) + ' ' + str(e.args) + '\n' + traceback.format_exc())

  ###########################################################################
      
  def turnOff(self):
    try:
      if self.is_connected():
        self.device.lua_execute('sleep(50); post_levent_to_ui("PressPowerButton")',
                                do_return=False)
    except chdkptp.PTPError as e:
      self.log('Failed to power off: PTPError: ' + str(e.args) + '\n' + traceback.format_exc() + '\nPTP Traceback:\n' + e.traceback)
    except Exception as e:
      self.log('Failed to power off: ' + str(e) + ' ' + str(e.args) + '\n' + traceback.format_exc())

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
