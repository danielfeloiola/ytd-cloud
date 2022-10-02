// quando o conteudo da dom estiver carregado
document.addEventListener('DOMContentLoaded', () => {

    // Liga o websocket
    var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port, {secure: true});
    console.log(io)


    // Cria o grafo
    var graph = {
        nodes: [],
        edges: []
    };

   
    // Inicia o sigma
    var s = new sigma(
    {
        graph: graph,
        renderer: {
            container: document.getElementById('sigma-container'),
            type: 'canvas'
        },
        settings: {
            minEdgeSize: 2,
            maxEdgeSize: 2,
            minNodeSize: 1,
            maxNodeSize: 6,
            drawLabels: false
        }
    });

    
    const getNodes = () => {
        const xhr = new XMLHttpRequest();
        xhr.open("GET", "/get_nodes");
        xhr.responseType = "json";
        xhr.onload = () => {
            const data = xhr.response;
            console.log(data)

            for (let point of data)
            {

                //cria o node
                node = {
                    id: point[0],
                    label: point[1],
                    x: Math.random(),
                    y: Math.random(),
                    size: point[3],
                    color: point[2]
                }

                // adiciona ao grafo
                s.graph.addNode(node)

            }
        };
        xhr.send();
    };
    getNodes();

    const getEdges = () => {
        const xhr = new XMLHttpRequest();
        xhr.open("GET", "/get_edges");
        xhr.responseType = "json";
        xhr.onload = () => {
            const data = xhr.response;
            console.log(data)

            let counter = 0;

            for (let point of data)
            {

                // cria um edge
                edge = {
                    id: counter,
                    source: point[0],
                    target: point[1],
                    color: "#707070",
                    size:1,
                    type:'arrow',
                }

                // adiciona ao grafo
                s.graph.addEdge(edge)

                counter++
            }
            // para criar um popup com dados do video

            s.bind("clickNode", function(e) {
                var node = e.data.node;
                var message = "<a href=https://youtu.be/" + node.id + " \"> " + node.label + "</a>";
                var popup = document.getElementById("myPopup");
                popup.innerHTML = message
        
                s.refresh()


            });

            // ajustes finais do grafo

            // Carrega o grafo no sigma
            s.graph.read(graph);

            // Faz o sigma criar o grafo
            s.refresh();


            // noverlap
            // Configura o noverlap layout
            var noverlapListener = s.configNoverlap({
                nodeMargin: 0.1,
                scaleNodes: 1.05,
                gridSize: 70,
                easing: 'quadraticInOut', // transicao da animacao
                duration: 1100   // duracao da animacao
            });


            // Bind
            noverlapListener.bind('start stop interpolate', function(e) {
                console.log(e.type);
                if(e.type === 'start') {
                    console.time('noverlap');
                }
                if(e.type === 'interpolate') {
                    console.timeEnd('noverlap');
                }
            });

            // inicia o algoritmo de espacialização
            s.startForceAtlas2({worker: true, barnesHutOptimize: false});

            // para o algoritmo apos 10s
            window.setTimeout(function() {s.killForceAtlas2(), s.startNoverlap()}, 10000 );

        };
        xhr.send();
    };
    getEdges();

});
