"""
Web Iface module
Template rendering for video and speed/cap
"""
from zope.interface import implements
from twisted.web import server
from twisted.web.resource import Resource
from twisted.internet import task
from twisted.web.iweb import IBodyProducer
from twisted.internet import defer


class Base(Resource):

    def render_GET(self, request):
        return """
        <html>
          <head>
            <title>Dis is Sumo.</title>
            <link rel="stylesheet"
            href="//code.jquery.com/ui/1.11.4/themes/smoothness/jquery-ui.css">
            <style>#slider { margin: 10px; }    </style>
            <style>#slider2 { margin: 10px; }    </style>
            <script src="//code.jquery.com/jquery-1.10.2.js"></script>
            <script src="//code.jquery.com/ui/1.11.4/jquery-ui.js"></script>
          </head>
          <body>
            <h1>Dis is Sumo.</h1>
            <img src="/video">
            <p> Speed </p>
            <div id="slider"></div>
            <p> Cap </p>
            <div id="slider2"></div>
             <script>
             $( "#slider" ).slider({step: 5, min: -100, max: 100,
                change: function(event, ui ) {
                     $.ajax({
                       type: "POST",
                       url: '/speed',
                       data: {speed: ui.value},
                     });
             }});
             $( "#slider2" ).slider({step: 5, min: -100, max: 100,
                change: function( event, ui ) {
                     $.ajax({
                       type: "POST",
                       url: '/speed',
                       data: {cap: ui.value},
                     });
             }});
             </script>
          </body>
        </html>
        """


class FrameProducer(object):
    """Send video frames at a constant rate"""
    implements(IBodyProducer)

    def __init__(self, state_holder):
        self.state = state_holder
        self.old_tf = 0

    def startProducing(self, request):
        d = defer.Deferred()
        task.LoopingCall(self.send_frame, request).start(0.05)
        return d

    def send_frame(self, request):
        if self.state.time_frame > self.old_tf:
            request.write(
                b'--frame\r\n' + b'Content-Type: image/jpeg\r\n\r\n'
                + self.state.frame + b'\r\n')
            self.old_tf = self.state.time_frame


class Video(Resource):
    isLeaf = True

    def __init__(self, state_holder):
        Resource.__init__(self)
        self.state = state_holder

    def render_GET(self, request):
        prod = FrameProducer(self.state)
        request.setHeader('Content-Type',
                          'multipart/x-mixed-replace; boundary=frame')
        prod.startProducing(request)
        return server.NOT_DONE_YET


class Speed(Resource):
    isLeaf = True

    def __init__(self, state_holder):
        Resource.__init__(self)
        self.state = state_holder

    def render_POST(self, request):
        # Update Sumo speed and/or cap
        speed = int(request.args.get('speed', [self.state.speed])[0])
        cap = int(request.args.get('cap', [self.state.cap])[0])
        print self.state.speed
        self.state.speed = speed
        print self.state.cap
        self.state.cap = cap
        return ''
