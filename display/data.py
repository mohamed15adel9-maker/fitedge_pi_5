from PIL import Image, ImageDraw, ImageFont

from display.oled_faces import oled, WIDTH, HEIGHT


def show_data(text):
    """
    Display text information on the 128x64 OLED.

    Used when a tool fetches personal or external data.
    """

    if text is None:
        return

    text = str(text).strip()

    if not text:
        return

    # Create a blank monochrome image
    image = Image.new("1", (WIDTH, HEIGHT), 0)
    draw = ImageDraw.Draw(image)

    # Use PIL's built-in small font
    font = ImageFont.load_default()

    # OLED is only 128x64, so keep the display compact.
    max_width = WIDTH - 4
    line_height = 10

    lines = []

    # -------------------------------------------------
    # Wrap text according to actual pixel width
    # -------------------------------------------------
    for paragraph in text.splitlines():

        paragraph = paragraph.strip()

        if not paragraph:
            continue

        words = paragraph.split()
        current_line = ""

        for word in words:

            test_line = (
                word
                if not current_line
                else current_line + " " + word
            )

            bbox = draw.textbbox(
                (0, 0),
                test_line,
                font=font,
            )

            width = bbox[2] - bbox[0]

            if width <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)

                current_line = word

        if current_line:
            lines.append(current_line)

    # -------------------------------------------------
    # Limit to what fits on the OLED
    # -------------------------------------------------
    max_lines = HEIGHT // line_height

    lines = lines[:max_lines]

    # -------------------------------------------------
    # Draw
    # -------------------------------------------------
    for index, line in enumerate(lines):

        y = index * line_height

        draw.text(
            (2, y),
            line,
            font=font,
            fill=1,
        )

    oled.display(image)