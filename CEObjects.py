class CERepository:
    def __init__(self):
        self.methods = None
        self.inserts = None
        self.sequences = None


class Well:
    def __init__(self, location, label=None, contents=None, shape=None, bounding_box=None):
        self.location = location
        self.label = label
        self.contents = contents
        self.shape = shape
        self.bound_box = bounding_box

    def __str__(self):
        return '{} at {} - SHAPE {} - BBOX {}'.format(self.label, self.location, self.shape, self.bound_box)


class Insert:
    def __init__(self, xy_upper_left=None, wells=None, label=None):
        self.wells = wells
        self.label = label
        self.xy_upper_left = xy_upper_left

    def __str__(self):
        separator = ','
        wells = ['{}'.format(str(well)) for well in self.wells]
        return_wells = separator.join(wells)
        return return_wells

    def get_well_xy(self, label):
        for well in self.wells:
            if well.label == label:
                return well.location
        else:
            return None

    def get_next_well_xy(self, label, increment):
        """Finds the next well based on how many times we 'increment' from the well with 'label'."""
        tolerance = 2
        # Sorry if you ever have to edit this Brae, the logic is a bit confusing.
        # Identify the starting well, based on the provided label.
        for well in self.wells:
            if well.label == label:

                wrong_wells = [well]
                next_well = None
                x, y, *_ = well.bound_box  # Save x and y of starting well.

                for _ in range(increment):
                    dy = 312
                    for other_well in self.wells:
                        # Check x and y of every other well to see who is next above the starting well.
                        ox, oy, *_ = other_well.bound_box
                        if 0 < (y - oy) < dy and abs(ox - x) < tolerance and other_well not in wrong_wells:
                            next_well = other_well
                            dy = y - oy
                    else:
                        if next_well not in wrong_wells:
                            wrong_wells.append(next_well)
                        else:
                            # If there is no next well above, reset x and y to be the location of well right of starting
                            dx = 584
                            right_well = None
                            for other_well in self.wells:
                                ox, oy, *_ = other_well.bound_box
                                if 0 < (ox - x) < dx and abs(oy - y) < tolerance and other_well not in wrong_wells:
                                    right_well = other_well
                                    dx = ox - x
                            if right_well:
                                next_well = right_well
                                wrong_wells.append(next_well)
                                x, y, *_ = right_well.bound_box
                                continue
                if next_well:
                    return next_well.location
                else:
                    return None
        else:
            return None


class Method:
    def __init__(self, insert, steps, label=None, ID=None):
        self.ID = ID
        self.steps = steps
        self.insert = insert
        self.label = label


class Sequence:
    def __init__(self, steps=None):
        self.steps = steps
