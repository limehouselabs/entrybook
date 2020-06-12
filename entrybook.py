#!/usr/bin/env python
import time, json, datetime
import urwid
from urwid import Columns, Filler, Text
from RFUID import rfid

def load_cards():
    with open('cards.json') as f:
        return json.load(f)

def load_present():
    with open('present.json', 'r') as f:
        return json.load(f)

def save_present(present):
    with open('present.json', 'w') as f:
        f.write(json.dumps(present))

def card_seen(cards, present, card):
    with open('log.txt', 'a') as f:
        if card in present:
            data = present[card]
            data['left'] = time.time()
            f.write(json.dumps(data) + '\n')
            del present[card]
        else:
            data = cards[card]
            data['arrived'] = time.time()
            f.write(json.dumps(data) + '\n')
            present[card] = data

        save_present(present)
        return present

def gen_columns(present, columns):
    names = 'Name\n\n' + '\n'.join([x['name'] for x in present.values()])
    orgs = 'Org\n\n' + '\n'.join([x['org'] for x in present.values()])
    times = 'Arrived\n\n' + '\n'.join([
        str(int((time.time() - x['arrived']) / 60)) + ' mins ago'
        for x in present.values()]
    )

    columns.contents = (
        (Filler(Text(names), 'top'), columns.options()),
        (Filler(Text(orgs), 'top'), columns.options()),
        (Filler(Text(times), 'top'), columns.options()),
    )

def update(loop, (cards, reader, columns, present)):
    try:
        for tag in reader.pn532.scan():
            uid = tag.uid.upper()
            present = card_seen(cards, present, uid)

    except rfid.NoCardException:
        pass

    gen_columns(present, columns)
    loop.set_alarm_in(0.2, update, user_data=(cards, reader, columns, present))


if __name__ == "__main__":
    cards = load_cards()
    present = load_present()

    reader = rfid.Pcsc.reader()
    reader.open()

    heading = urwid.Text(('banner', u" Currently signed in "), align='center')
    columns = urwid.Columns((
        Filler(Text('Name'), 'top'),
        Filler(Text('Org'), 'top'),
        Filler(Text('Time'), 'top'),
    ))
    frame = urwid.Frame(columns, header=heading)

    loop = urwid.MainLoop(frame)
    loop.screen.set_terminal_properties(colors=256)
    loop.set_alarm_in(0.2, update, user_data=(cards, reader, columns, present))
    loop.run()
