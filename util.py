import cv2
import yaml
import numpy as np
import pyautogui


def click_event(event, x, y, flags, params):
    global click_event_return
    if event == cv2.EVENT_LBUTTONDOWN:
        click_event_return.append(np.array([x, y]))


def screenshot_cv():
    img = pyautogui.screenshot()
    cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    return cv_img


def click_on_screenshot(img, alert_msg=""):
    cv2.imshow('Screenshot', img)
    cv2.setMouseCallback('Screenshot', click_event)
    pyautogui.alert(alert_msg)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def resolution_string_to_int(resolution):
    return [int(x) for x in resolution.split('x')]


def read_yaml(path):
    yaml_dict = None
    with open(path, "r") as f:
        try:
            yaml_dict = yaml.safe_load(f)
        except yaml.YAMLError as exc:
            print(exc)
            exit()
    return yaml_dict


def adjust_to_width_height_difference(d, wd, hd):
    """Subtract .5 width_difference from first dimension of coordinates. Skip 'upper-left-cell' because it is
    positioned at (0, 0) and thus unaffected by this adjustment.
    """
    for k, v in d.items():
        if isinstance(v, dict):
            adjust_to_width_height_difference(v, wd, hd)
        else:
            if isinstance(v, list):
                if k != 'upper-left-cell':
                    d[k][0] = v[0] - round(wd / 2.0)
                d[k][1] = v[1] - round(hd / 2.0)


def adjust_to_scale_difference(d, sf):
    """Multiply every layout value with the required rescaling factor. We skip entries under 'dropdown' because they
    are unaffected by this adjustment.
    """
    for k, v in d.items():
        if isinstance(v, dict):
            if k == 'dropdown':
                return
            adjust_to_scale_difference(v, sf)
        else:
            if isinstance(v, list):
                d[k][0] = round(v[0] * sf)
                d[k][1] = round(v[1] * sf)
            else:
                d[k] = round(v * sf)


def gcd(a, b):
    if b == 0:
        return a
    return gcd(b, a % b)


def read_adjusted_layout(trg_res, layout_config_path):
    src_res = "3440x1440"
    layout_yaml_dict = read_yaml(layout_config_path)
    if src_res in layout_yaml_dict.keys():
        layout = layout_yaml_dict[src_res]
    else:
        raise Exception(f"Could not find valid layout description for resolution {src_res}!")

    if trg_res == src_res:
        return layout

    src_width, src_height = resolution_string_to_int(src_res)
    trg_width, trg_height = resolution_string_to_int(trg_res)
    res_gcd = gcd(trg_height, trg_width)
    aspect_ratio = f"{int(trg_width / res_gcd)}:{int(trg_height / res_gcd)}"
    print(aspect_ratio)
    if aspect_ratio != '16:9' and aspect_ratio != '7:3':  # 21:9
        # 16:10 e.g. results in black bars at top and bottom. We have to add height_difference / 2.0 as offset to
        # second coordinate dimension values in that case.
        scale_factor = (trg_height - trg_height / 10) / src_height
        height_difference = round(src_height * scale_factor - trg_height)
    else:
        height_difference = 0
        scale_factor = trg_height / src_height
    width_difference = round(src_width * scale_factor - trg_width)
    print(scale_factor, width_difference, height_difference)

    adjust_to_width_height_difference(layout, width_difference, height_difference)
    adjust_to_scale_difference(layout, scale_factor)

    print(yaml.dump(layout, allow_unicode=True, default_flow_style=False))

    return layout
