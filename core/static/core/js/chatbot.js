(function(d, t) {
    var v = d.createElement(t), s = d.getElementsByTagName(t)[0];
    v.onload = function() {
      window.voiceflow.chat.load({
        verify: { projectID: '6ada2e7bb5d63caef1f09ae1' },
        url: 'https://general-runtime.voiceflow.com',
        voice: {
          url: 'https://runtime-api.voiceflow.com'
        },
        environmentID: 'main',
        versionVariant: 'published'
      });
    }
    v.src = 'https://cdn.voiceflow.com/widget-next/bundle.mjs'; v.type = 'text/javascript'; s.parentNode.insertBefore(v, s);
})(document, 'script');