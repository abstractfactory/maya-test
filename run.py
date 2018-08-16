from nose.tools import with_setup, assert_equals, assert_not_equals
from maya import standalone, cmds

a = "Root"
b = "Mid"
c = "Tip"


def setup():
    """Called automatically on start-up"""
    standalone.initialize()


def new():
    # Build Scene
    # o     o
    #  \   /
    #   \ /
    #    o
    #
    cmds.file(new=True, force=True)
    cmds.joint(name=a, position=(0, 0, 20))
    cmds.joint(name=b, position=(0, 0, 0), relative=False)
    cmds.joint(name=c, position=(0, 10, -20), relative=False)
    handle, eff = cmds.ikHandle(
        solver="ikRPsolver",
        startJoint=a,
        endEffector=c,
    )


@with_setup(new)
def test_bug():
    """Test bug

    Ensure that the bug occurs

    """

    assert_equals(cmds.getAttr(a + ".rx"), 0.0)
    assert_equals(cmds.getAttr(a + ".rx", time=1), 0.0)

    # Move handle
    cmds.move(0, 15, -10, "|ikHandle1")

    assert_equals(round(cmds.getAttr(a + ".rx"), 0), -14.0)

    # This is the bug
    assert_not_equals(round(cmds.getAttr(a + ".rx", time=1), 0), -14.0)


@with_setup(new)
def test_workaround():
    """Test workaround

    Workaround the issue by querying each attribute twice

    """

    def getAttr(attr, time):
        cmds.getAttr(attr, time=time - 1)
        return cmds.getAttr(attr, time=time)

    assert_equals(cmds.getAttr(a + ".rx"), 0.0)
    assert_equals(cmds.getAttr(a + ".rx", time=1), 0.0)

    # Move handle
    cmds.move(0, 15, -10, "|ikHandle1")

    assert_equals(round(cmds.getAttr(a + ".rx"), 0), -14.0)
    assert_equals(round(getAttr(a + ".rx", time=1), 0), -14.0)


@with_setup(new)
def test_optimisation():
    """Test optimisation

    If the cause of the bug is ikHandle, then once an attribute has
    been called twice and triggered the evaluation of ikHandle, the
    next dependent node can be called just once.

    """

    def getAttr(attr, time):
        cmds.getAttr(attr, time=time - 1)
        return cmds.getAttr(attr, time=time)

    assert_equals(cmds.getAttr(a + ".rx"), 0.0)
    assert_equals(cmds.getAttr(a + ".rx", time=1), 0.0)

    # Move handle
    cmds.move(0, 15, -10, "|ikHandle1")

    assert_equals(round(cmds.getAttr(a + ".rx"), 0), -14.0)
    assert_equals(round(getAttr(a + ".rx", time=1), 0), -14.0)

    # The above call also enables this other node to evaluate properly
    # Which means we only need to call the special function once
    # per IK node.
    assert_equals(round(cmds.getAttr(b + ".rx", time=1), 0), 49.0)

    cmds.move(0, 15, -15, "|ikHandle1")

    # Once out-of-date again, the workaround must be applied
    assert_not_equals(round(cmds.getAttr(a + ".rx", time=1), 0), -4.0)
    assert_equals(round(getAttr(a + ".rx", time=1), 0), -4.0)
