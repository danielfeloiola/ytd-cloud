// quando o conteudo da dom estiver carregado
document.addEventListener('DOMContentLoaded', () => {

    // Liga o websocket
    var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);


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
            minEdgeSize: 0.1,
            maxEdgeSize: 2,
            minNodeSize: 1,
            maxNodeSize: 4,
            minArrowSize: 10
        }
    });


    // Pede pelos dados
    socket.emit('get_nodes');
    socket.emit('get_edges');


    // Ao receber os dados de um node
    socket.on('get_nodes', data =>
    {

        for (let point of data)
        {

            //cria o node
            node = {
                id: point[0],
                label: point[1],
                x: Math.random(),
                y: Math.random(),
                size: 3,
                color: '#000000'
            }

            // adiciona ao grafo
            s.graph.addNode(node)

        }

    });

    // Ao receber os dados de um edge
    socket.on('get_edges', data =>
    {
        let counter = 0;

        for (let point of data)
        {

            // cria um edge
            edge = {
                id: counter,
                source: point[0],
                target: point[1],
                color: "#404040",
                size:1,
                type:'arrow',
            }

            // adiciona ao grafo
            s.graph.addEdge(edge)

            counter++
        }

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
            gridSize: 750,
            easing: 'quadraticInOut', // transicao da animacao
            duration: 1000   // duracao da animacao
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


    });


});
