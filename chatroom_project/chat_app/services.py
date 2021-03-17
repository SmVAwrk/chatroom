
def invite_handler(invite):
    if invite.is_accepted:
        invite.room.members.add(invite.invite_object)
        invite.delete()
    elif invite.is_accepted is False:
        invite.delete()