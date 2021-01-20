import time
import threading
# PARAMETERS
target_x = 871
target_y = 585
rgb_chnl = 'B'
fluor_channel = 4
wait = 0.25
exp = 500
_old_exp=10
_old_bin = 2
_old_channel = 1
light_channel = 'cyan'
bins = 2
obj_60x = 0.0001927525057825752
conversion = obj_60x

def te300_presnap(ce_sys, intensity=1):
    ce_sys.excitation_wheel.set_intensity(['red','blue','green','cyan','uv','teal'],intensity)

def te300_postsnap(ce_sys, intensity=0):
    ce_sys.excitation_wheel.set_intensity(['red','blue','green','cyan','uv','teal'],intensity)

def pre_fluoresence(ce_system,rgb=rgb_chnl,bins=bins,fluor_channel=fluor_channel,
                    wait=wait, exp=exp,light_channel=light_channel, auto_shutter=False):
    # SNAP a FLUOR IMAGE
    # Set to new values
    ce_system.inlet_rgb.turn_off_channel(rgb)
    ce_system.camera.stop()
    ce_system.filter_wheel.set_channel(fluor_channel)
    ce_system.excitation_wheel.set_channel([light_channel])
    ce_system.camera.set_exposure(exp)
    #_old_exp = ce_system.camera.exposure
    ce_system.camera.set_binning(bins)
    #_old_bin = ce_system.camera.bin_size
    time.sleep(wait)
    
def post_fluoresence(ce_system,rgb_channel=rgb_chnl, old_exp=_old_exp,
                     old_bin=_old_bin,old_channel=_old_channel,
                     auto_shutter=False):
    # Return to old values
    ce_system.camera.set_exposure(old_exp)
    #ce_system.camera.set_binning(old_bin)
    ce_system.filter_wheel.set_channel(old_channel)
    ce_system.inlet_rgb.turn_on_channel(rgb_channel)
    ce_system.excitation_wheel.set_channel([])
    ce_system.camera.set_binning(old_bin)
    ce_system.camera.continuous_snap()
 
def get_cap_height(obj_height, cap_difference):
    cap_height = obj_height - cap_difference
    return cap_height

def move_to_blob(ce_system, df):
    if df.shape[0] > 0:
        y=df['centroid-0'][0]*bins
        x=df['centroid-1'][0]*bins

        movex = (x-target_x)*conversion
        movey = (y-target_y)*conversion
        ce_system.xy_stage.set_rel_x(movex)
        ce_system.xy_stage.set_rel_y(-movey)
        
def limited_fire(ce_system, gravity_drop, voltage_level, injection_time, delta_z=0.002, delta_x=0.001, delta_time=0.25, under_pulses=2, delay=0.3):
    time.sleep(delay)
    print('Fire')
    ce_system.outlet_z.set_rel_z(-gravity_drop)
    ce_system.high_voltage.set_voltage(voltage_level)
    ce_system.high_voltage.start()
    start_time = time.time()
    
    ce_system.lysis_laser.laser_fire()
    ce_system.objective.set_rel_z(-delta_z*under_pulses)

    while time.time()-start_time < injection_time:
        if time.time()-start_time < 3:
            ce_system.objective.set_rel_z(delta_z)
            ce_system.xy_stage.set_rel_x(delta_x)
            ce_system.lysis_laser.laser_fire()
        time.sleep(delta_time)
    ce_system.high_voltage.stop()
    print(f"Finished {time.time()-start_time}")
    ce_system.outlet_z.set_rel_z(gravity_drop)

def initialize(ce_system):
    ce_system.camera._presnap_callbacks=[]
    ce_system.camera._postsnap_callbacks=[]
    ce_system.camera.add_presnap_callback(te300_presnap,ce_sys=ce_system)
    ce_system.camera.add_postsnap_callback(te300_postsnap, ce_sys=ce_system)
